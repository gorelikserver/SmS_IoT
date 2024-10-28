from typing import Dict, List
import time
from datetime import datetime
from ..terminal.simplex_terminal import SimplexTerminal
from .point_status import PointStatus, StatusChange
from ..utils.logging import get_logger

logger = get_logger(__name__)


class StatusMonitor:
    def __init__(self, terminal: SimplexTerminal, poll_interval: int = 60):
        self.terminal = terminal
        self.poll_interval = poll_interval
        self.current_states: Dict[str, PointStatus] = {}
        self.running = False

    def detect_changes(self, new_states: Dict[str, PointStatus]) -> List[StatusChange]:
        """Detect changes between current and new states."""
        changes = []

        # Check for new or changed points
        for point_id, new_status in new_states.items():
            if point_id not in self.current_states:
                changes.append(StatusChange('NEW', None, new_status))
            elif new_status.status != self.current_states[point_id].status:
                changes.append(StatusChange('CHANGED', self.current_states[point_id], new_status))

        # Check for cleared points
        for point_id in self.current_states:
            if point_id not in new_states:
                changes.append(StatusChange('CLEARED', self.current_states[point_id], None))

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
                logger.error(f"Error during monitoring: {e}")
                if not self.terminal.login(passcode):
                    logger.error("Failed to relogin after error")
                    break

    def _handle_changes(self, changes: List[StatusChange]):
        """Handle detected changes."""
        for change in changes:
            if change.change_type == 'NEW':
                logger.info(f"New point: {change.new_status.point_id} - {change.new_status.status}")
            elif change.change_type == 'CHANGED':
                logger.info(
                    f"Status changed: {change.new_status.point_id} "
                    f"from {change.previous_status.status} to {change.new_status.status}"
                )
            elif change.change_type == 'CLEARED':
                logger.info(f"Point cleared: {change.previous_status.point_id}")

            # Here you would add code to send changes to your API

    def stop(self):
        """Stop the monitoring loop."""
        self.running = False