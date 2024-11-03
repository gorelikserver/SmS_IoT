from typing import Dict, List
import time
from ..terminal.simplex_terminal import SimplexTerminal
from .point_status import PointStatus, StatusChange
from ..points import PointsManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class StatusMonitor:
    def __init__(self, terminal: SimplexTerminal, points_manager: PointsManager, poll_interval: int = 60):
        self.terminal = terminal
        self.points_manager = points_manager
        self.poll_interval = poll_interval
        self.current_states: Dict[str, PointStatus] = {}
        self.running = False

    def detect_changes(self, new_states: Dict[str, PointStatus]) -> List[StatusChange]:
        """Detect changes between current and new states."""
        changes = []

        # Check for new or changed points
        for point_id, new_status in new_states.items():
            # Update point status in points manager
            self.points_manager.update_point_status(point_id, new_status.status)

            if point_id not in self.current_states:
                enriched_status = self.points_manager.get_enriched_status(new_status)
                changes.append(StatusChange(
                    'NEW',
                    None,
                    new_status,  # Keep original PointStatus object
                    enriched_data=enriched_status  # Add enriched data separately
                ))
            elif new_status.status != self.current_states[point_id].status:
                old_enriched = self.points_manager.get_enriched_status(self.current_states[point_id])
                new_enriched = self.points_manager.get_enriched_status(new_status)
                changes.append(StatusChange(
                    'CHANGED',
                    self.current_states[point_id],
                    new_status,
                    enriched_data=new_enriched,
                    previous_enriched_data=old_enriched
                ))

        # Check for cleared points
        for point_id in self.current_states:
            if point_id not in new_states:
                old_enriched = self.points_manager.get_enriched_status(self.current_states[point_id])
                changes.append(StatusChange(
                    'CLEARED',
                    self.current_states[point_id],
                    None,
                    previous_enriched_data=old_enriched
                ))

        return changes

    def start_monitoring(self, passcode: str):
        """Start the monitoring loop."""
        if not self.terminal.login(passcode):
            logger.error("Failed to login")
            return

        self.running = True
        logger.info("Starting monitoring loop")

        while self.running:
            try:
                points_data = self.terminal.get_clist()
                new_states = {
                    p['id']: PointStatus.from_clist_line(p['id'], p['status'])
                    for p in points_data
                }

                changes = self.detect_changes(new_states)
                self._handle_changes(changes)
                self.current_states = new_states

                time.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Error during monitoring: {e}", exc_info=True)
                if not self.terminal.login(passcode):
                    logger.error("Failed to relogin after error")
                    break

    def _handle_changes(self, changes: List[StatusChange]):
        """Handle detected changes."""
        for change in changes:
            if change.change_type == 'NEW':
                description = change.enriched_data.get('description', 'No description')
                logger.info(
                    f"New point: {change.new_status.point_id} - {change.new_status.status} "
                    f"({description})"
                )
            elif change.change_type == 'CHANGED':
                description = change.enriched_data.get('description', 'No description')
                logger.info(
                    f"Status changed: {change.new_status.point_id} "
                    f"from {change.previous_status.status} to {change.new_status.status} "
                    f"({description})"
                )
            elif change.change_type == 'CLEARED':
                description = change.previous_enriched_data.get('description', 'No description')
                logger.info(
                    f"Point cleared: {change.previous_status.point_id} "
                    f"({description})"
                )

    def stop(self):
        """Stop the monitoring loop."""
        self.running = False