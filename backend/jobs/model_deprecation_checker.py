"""
Model Deprecation Checker
Automated job to detect deprecated models and update approved models table
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.repositories.agent_model_repository import (
    ApprovedModelProviderModel,
    AgentModelConfigModel,
)


@dataclass
class ModelCheckResult:
    """Result of checking a single model"""
    provider: str
    model_name: str
    status: str  # "active", "deprecated", "unknown"
    error_message: str | None = None
    replacement_model: str | None = None


@dataclass
class DeprecationReport:
    """Report of deprecation check results"""
    timestamp: datetime
    checked_models: int
    active_models: int
    deprecated_models: int
    unknown_models: int
    details: list[ModelCheckResult]
    suggested_updates: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "checked": self.checked_models,
                "active": self.active_models,
                "deprecated": self.deprecated_models,
                "unknown": self.unknown_models,
            },
            "deprecated_models": [
                {
                    "provider": r.provider,
                    "model": r.model_name,
                    "error": r.error_message,
                    "replacement": r.replacement_model,
                }
                for r in self.details if r.status == "deprecated"
            ],
            "suggested_updates": self.suggested_updates,
        }


class ModelDeprecationChecker:
    """Check model availability across providers and detect deprecations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def check_all_models(self) -> DeprecationReport:
        """
        Check all approved models for deprecation

        Returns:
            DeprecationReport with results and suggested updates
        """
        # Get all approved models
        stmt = select(ApprovedModelProviderModel).where(
            ApprovedModelProviderModel.approved == True
        )
        result = await self.session.execute(stmt)
        approved_models = result.scalars().all()

        results: list[ModelCheckResult] = []

        # Check each model
        for model in approved_models:
            check_result = await self._check_model(model.provider, model.model_name)
            results.append(check_result)

        # Generate report
        active_count = sum(1 for r in results if r.status == "active")
        deprecated_count = sum(1 for r in results if r.status == "deprecated")
        unknown_count = sum(1 for r in results if r.status == "unknown")

        # Generate suggested updates
        suggested_updates = await self._generate_suggested_updates(results)

        return DeprecationReport(
            timestamp=datetime.utcnow(),
            checked_models=len(results),
            active_models=active_count,
            deprecated_models=deprecated_count,
            unknown_models=unknown_count,
            details=results,
            suggested_updates=suggested_updates,
        )

    async def _check_model(self, provider: str, model_name: str) -> ModelCheckResult:
        """
        Check if a specific model is available

        Args:
            provider: Provider name (openai, anthropic)
            model_name: Model identifier

        Returns:
            ModelCheckResult with status and details
        """
        if provider.lower() == "openai":
            return await self._check_openai_model(model_name)
        elif provider.lower() == "anthropic":
            return await self._check_anthropic_model(model_name)
        else:
            return ModelCheckResult(
                provider=provider,
                model_name=model_name,
                status="unknown",
                error_message=f"Unsupported provider: {provider}",
            )

    async def _check_openai_model(self, model_name: str) -> ModelCheckResult:
        """Check OpenAI model availability"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.settings.openai_api_key)

            # Try a minimal completion to test model availability
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )

            return ModelCheckResult(
                provider="openai",
                model_name=model_name,
                status="active",
            )

        except Exception as e:
            error_msg = str(e)

            # Check if it's a 404/not found error
            if "404" in error_msg or "not_found" in error_msg.lower():
                return ModelCheckResult(
                    provider="openai",
                    model_name=model_name,
                    status="deprecated",
                    error_message=error_msg,
                    replacement_model=self._suggest_openai_replacement(model_name),
                )

            return ModelCheckResult(
                provider="openai",
                model_name=model_name,
                status="unknown",
                error_message=error_msg,
            )

    async def _check_anthropic_model(self, model_name: str) -> ModelCheckResult:
        """Check Anthropic model availability"""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)

            # Try a minimal message to test model availability
            response = await client.messages.create(
                model=model_name,
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}],
            )

            return ModelCheckResult(
                provider="anthropic",
                model_name=model_name,
                status="active",
            )

        except Exception as e:
            error_msg = str(e)

            # Check if it's a 404/not found error
            if "404" in error_msg or "not_found" in error_msg.lower():
                return ModelCheckResult(
                    provider="anthropic",
                    model_name=model_name,
                    status="deprecated",
                    error_message=error_msg,
                    replacement_model=self._suggest_anthropic_replacement(model_name),
                )

            return ModelCheckResult(
                provider="anthropic",
                model_name=model_name,
                status="unknown",
                error_message=error_msg,
            )

    def _suggest_openai_replacement(self, deprecated_model: str) -> str | None:
        """Suggest a replacement for deprecated OpenAI model"""
        # Map old models to new ones
        replacements = {
            "gpt-3.5-turbo": "gpt-4o-mini",
            "gpt-4": "gpt-4o",
        }

        for old_pattern, new_model in replacements.items():
            if old_pattern in deprecated_model:
                return new_model

        return None

    def _suggest_anthropic_replacement(self, deprecated_model: str) -> str | None:
        """Suggest a replacement for deprecated Anthropic model"""
        # Map Claude 3.5 to Claude 4
        if "claude-3-5-sonnet" in deprecated_model or "claude-3-sonnet" in deprecated_model:
            return "claude-sonnet-4-20250514"
        elif "claude-3-5-haiku" in deprecated_model or "claude-3-haiku" in deprecated_model:
            return "claude-haiku-4-20250514"
        elif "claude-3-opus" in deprecated_model:
            return "claude-opus-4-20250514"

        return None

    async def _generate_suggested_updates(
        self, results: list[ModelCheckResult]
    ) -> list[dict[str, str]]:
        """
        Generate suggested updates based on check results

        Args:
            results: List of model check results

        Returns:
            List of suggested database updates
        """
        suggestions = []

        for result in results:
            if result.status == "deprecated" and result.replacement_model:
                # Check if replacement model already exists
                stmt = select(ApprovedModelProviderModel).where(
                    ApprovedModelProviderModel.provider == result.provider,
                    ApprovedModelProviderModel.model_name == result.replacement_model,
                )
                existing = await self.session.execute(stmt)
                if not existing.scalar_one_or_none():
                    suggestions.append(
                        {
                            "action": "add_model",
                            "provider": result.provider,
                            "model_name": result.replacement_model,
                            "replaces": result.model_name,
                        }
                    )

                # Suggest marking old model as deprecated
                suggestions.append(
                    {
                        "action": "mark_deprecated",
                        "provider": result.provider,
                        "model_name": result.model_name,
                        "replacement": result.replacement_model,
                    }
                )

        return suggestions

    async def apply_suggested_updates(
        self, report: DeprecationReport, auto_approve: bool = False
    ) -> dict[str, Any]:
        """
        Apply suggested updates to the database

        Args:
            report: Deprecation report with suggestions
            auto_approve: If True, apply all updates automatically

        Returns:
            Summary of applied updates
        """
        if not auto_approve:
            return {
                "status": "pending_approval",
                "message": "Updates require manual approval",
                "suggestions": report.suggested_updates,
            }

        applied = []
        failed = []

        for suggestion in report.suggested_updates:
            try:
                if suggestion["action"] == "mark_deprecated":
                    # Mark model as deprecated
                    stmt = (
                        update(ApprovedModelProviderModel)
                        .where(
                            ApprovedModelProviderModel.provider == suggestion["provider"],
                            ApprovedModelProviderModel.model_name == suggestion["model_name"],
                        )
                        .values(
                            deprecated=True,
                            updated_at=datetime.utcnow(),
                        )
                    )
                    await self.session.execute(stmt)
                    applied.append(suggestion)

                elif suggestion["action"] == "add_model":
                    # Add new model (would need more metadata)
                    # For now, just log it as requiring manual addition
                    failed.append(
                        {
                            **suggestion,
                            "reason": "Adding new models requires manual metadata",
                        }
                    )

            except Exception as e:
                failed.append({**suggestion, "error": str(e)})

        if applied:
            await self.session.commit()

        return {
            "status": "completed",
            "applied": applied,
            "failed": failed,
            "total_suggestions": len(report.suggested_updates),
            "applied_count": len(applied),
            "failed_count": len(failed),
        }


async def check_model_deprecations(session: AsyncSession) -> DeprecationReport:
    """
    Convenience function to check all models for deprecation

    Args:
        session: Database session

    Returns:
        DeprecationReport with results
    """
    checker = ModelDeprecationChecker(session)
    return await checker.check_all_models()
