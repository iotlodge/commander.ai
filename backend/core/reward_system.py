"""
Reward System - Gamification for Agent Optimization

Calculates reward points and penalties based on performance metrics.
Incentivizes high-quality, efficient, and user-satisfying outputs.

Rewards consider:
- Task completion (base points)
- Quality scores (accuracy, relevance, completeness)
- Speed and efficiency
- Cost optimization
- User satisfaction ratings
- Peer recognition (other agents' evaluations)

Penalties for:
- Failed tasks
- Excessive cost
- Slow execution
- Poor user ratings
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RewardCalculation:
    """Result of reward/penalty calculation"""
    total_reward: int
    base_reward: int
    quality_bonus: int
    speed_bonus: int
    cost_bonus: int
    user_bonus: int
    peer_bonus: int
    penalties: int
    net_reward: int  # total_reward - penalties

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for storage"""
        return {
            "total_reward": self.total_reward,
            "base_reward": self.base_reward,
            "quality_bonus": self.quality_bonus,
            "speed_bonus": self.speed_bonus,
            "cost_bonus": self.cost_bonus,
            "user_bonus": self.user_bonus,
            "peer_bonus": self.peer_bonus,
            "penalties": self.penalties,
            "net_reward": self.net_reward,
        }


class RewardSystem:
    """
    Calculate rewards and penalties for agent performance

    Point System:
    - Base completion: 10 points
    - Quality bonus: 0-50 points (based on overall_score)
    - Speed bonus: 0-20 points (faster = more points)
    - Cost efficiency: 0-30 points (cheaper = more points)
    - User satisfaction: 0-40 points (5-star rating)
    - Peer recognition: 0-25 points (avg peer eval)
    """

    # Reward weights
    REWARD_WEIGHTS = {
        "task_completion": 10,
        "quality_bonus": 50,
        "speed_bonus": 20,
        "cost_efficiency": 30,
        "user_satisfaction": 40,
        "peer_recognition": 25,
    }

    # Penalty amounts
    PENALTY_AMOUNTS = {
        "task_failed": 30,
        "excessive_cost": 10,  # Per $0.10 over threshold
        "timeout": 5,          # Per 10 seconds over threshold
        "poor_rating": 15,     # Per star below 3
    }

    # Thresholds
    COST_THRESHOLD = 0.50  # $0.50
    DURATION_THRESHOLD = 120  # 2 minutes

    def calculate_reward(
        self,
        task_status: str,
        overall_score: float,
        duration_seconds: float,
        total_cost: float,
        user_rating: Optional[int] = None,
        peer_evaluations: Optional[list] = None
    ) -> RewardCalculation:
        """
        Calculate total reward points for a task

        Args:
            task_status: "COMPLETED", "FAILED", etc.
            overall_score: Quality score (0-1)
            duration_seconds: Task execution time
            total_cost: Estimated cost in dollars
            user_rating: Optional 1-5 star rating
            peer_evaluations: Optional list of peer eval scores (0-1)

        Returns:
            RewardCalculation with detailed breakdown
        """
        # Base reward (only for completed tasks)
        base_reward = (
            self.REWARD_WEIGHTS["task_completion"]
            if task_status == "COMPLETED"
            else 0
        )

        # Quality bonus (0-50 points)
        quality_bonus = int(overall_score * self.REWARD_WEIGHTS["quality_bonus"])

        # Speed bonus (faster = more points)
        speed_bonus = self._calculate_speed_bonus(duration_seconds)

        # Cost efficiency bonus
        cost_bonus = self._calculate_cost_bonus(total_cost, overall_score)

        # User satisfaction bonus
        user_bonus = (
            int((user_rating / 5.0) * self.REWARD_WEIGHTS["user_satisfaction"])
            if user_rating
            else 0
        )

        # Peer recognition bonus
        peer_bonus = self._calculate_peer_bonus(peer_evaluations)

        # Total rewards
        total_reward = (
            base_reward +
            quality_bonus +
            speed_bonus +
            cost_bonus +
            user_bonus +
            peer_bonus
        )

        # Calculate penalties
        penalties = self._calculate_penalties(
            task_status=task_status,
            duration_seconds=duration_seconds,
            total_cost=total_cost,
            user_rating=user_rating
        )

        # Net reward (can be negative!)
        net_reward = total_reward - penalties

        result = RewardCalculation(
            total_reward=total_reward,
            base_reward=base_reward,
            quality_bonus=quality_bonus,
            speed_bonus=speed_bonus,
            cost_bonus=cost_bonus,
            user_bonus=user_bonus,
            peer_bonus=peer_bonus,
            penalties=penalties,
            net_reward=net_reward
        )

        logger.info(
            f"Reward calculated: {net_reward} points "
            f"(rewards: {total_reward}, penalties: {penalties})"
        )

        return result

    def _calculate_speed_bonus(self, duration_seconds: float) -> int:
        """
        Calculate speed bonus based on execution time

        Faster tasks get more points:
        - < 5 seconds: 20 points (max)
        - < 10 seconds: 15 points
        - < 30 seconds: 10 points
        - < 60 seconds: 5 points
        - >= 60 seconds: 0 points
        """
        if duration_seconds < 5:
            return self.REWARD_WEIGHTS["speed_bonus"]
        elif duration_seconds < 10:
            return int(self.REWARD_WEIGHTS["speed_bonus"] * 0.75)
        elif duration_seconds < 30:
            return int(self.REWARD_WEIGHTS["speed_bonus"] * 0.50)
        elif duration_seconds < 60:
            return int(self.REWARD_WEIGHTS["speed_bonus"] * 0.25)
        else:
            return 0

    def _calculate_cost_bonus(self, total_cost: float, quality_score: float) -> int:
        """
        Calculate cost efficiency bonus

        Rewards low cost relative to quality:
        - If cost < $0.05: Full bonus (30 points)
        - If cost < $0.10: 75% bonus (22 points)
        - If cost < $0.25: 50% bonus (15 points)
        - If cost < $0.50: 25% bonus (7 points)
        - If cost >= $0.50: 0 points

        Also scales with quality (low cost + low quality = lower bonus)
        """
        max_bonus = self.REWARD_WEIGHTS["cost_efficiency"]

        # Base cost bonus
        if total_cost < 0.05:
            cost_bonus = max_bonus
        elif total_cost < 0.10:
            cost_bonus = int(max_bonus * 0.75)
        elif total_cost < 0.25:
            cost_bonus = int(max_bonus * 0.50)
        elif total_cost < 0.50:
            cost_bonus = int(max_bonus * 0.25)
        else:
            cost_bonus = 0

        # Scale by quality (prevent gaming with cheap but bad outputs)
        quality_multiplier = max(quality_score, 0.5)  # Minimum 50% scaling
        return int(cost_bonus * quality_multiplier)

    def _calculate_peer_bonus(self, peer_evaluations: Optional[list]) -> int:
        """
        Calculate peer recognition bonus

        Average of peer evaluation scores * 25 points
        """
        if not peer_evaluations:
            return 0

        # Extract scores from peer evaluations
        scores = []
        for eval_data in peer_evaluations:
            if isinstance(eval_data, dict) and "score" in eval_data:
                scores.append(eval_data["score"])
            elif isinstance(eval_data, (int, float)):
                scores.append(float(eval_data))

        if not scores:
            return 0

        avg_peer_score = sum(scores) / len(scores)
        return int(avg_peer_score * self.REWARD_WEIGHTS["peer_recognition"])

    def _calculate_penalties(
        self,
        task_status: str,
        duration_seconds: float,
        total_cost: float,
        user_rating: Optional[int]
    ) -> int:
        """
        Calculate penalties for poor performance

        Penalties for:
        - Failed tasks: 30 points
        - Excessive cost (> $0.50): 10 points per $0.10 over
        - Timeout (> 2 minutes): 5 points per 10 seconds over
        - Poor user rating (< 3 stars): 15 points per star below 3
        """
        penalty = 0

        # Failed task
        if task_status == "FAILED":
            penalty += self.PENALTY_AMOUNTS["task_failed"]
            logger.debug(f"Task failed penalty: {self.PENALTY_AMOUNTS['task_failed']}")

        # Excessive cost
        if total_cost > self.COST_THRESHOLD:
            excess = total_cost - self.COST_THRESHOLD
            cost_penalty = int((excess / 0.10) * self.PENALTY_AMOUNTS["excessive_cost"])
            penalty += cost_penalty
            logger.debug(f"Excessive cost penalty: {cost_penalty} (${total_cost:.2f})")

        # Timeout
        if duration_seconds > self.DURATION_THRESHOLD:
            excess_seconds = duration_seconds - self.DURATION_THRESHOLD
            timeout_penalty = int((excess_seconds / 10) * self.PENALTY_AMOUNTS["timeout"])
            penalty += timeout_penalty
            logger.debug(f"Timeout penalty: {timeout_penalty} ({duration_seconds:.1f}s)")

        # Poor user rating
        if user_rating and user_rating < 3:
            stars_below = 3 - user_rating
            rating_penalty = stars_below * self.PENALTY_AMOUNTS["poor_rating"]
            penalty += rating_penalty
            logger.debug(f"Poor rating penalty: {rating_penalty} ({user_rating} stars)")

        return penalty


# Convenience function for calculating rewards from task metadata

def calculate_task_reward(task_metadata: Dict[str, Any]) -> RewardCalculation:
    """
    Calculate reward from task metadata

    Args:
        task_metadata: Task metadata dict with scores, metrics, etc.

    Returns:
        RewardCalculation
    """
    system = RewardSystem()

    return system.calculate_reward(
        task_status=task_metadata.get("status", "UNKNOWN"),
        overall_score=task_metadata.get("overall_score", 0.5),
        duration_seconds=task_metadata.get("duration_seconds", 60.0),
        total_cost=task_metadata.get("estimated_cost", 0.0),
        user_rating=task_metadata.get("user_rating"),
        peer_evaluations=task_metadata.get("peer_evaluations", [])
    )
