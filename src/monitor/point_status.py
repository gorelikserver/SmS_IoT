from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PointStatus:
    point_id: str
    status: str
    timestamp: datetime
    point_type: str
    state_type: str
    is_active: bool
    is_acknowledged: bool

    @classmethod
    def from_clist_line(cls, point_id: str, status: str) -> 'PointStatus':
        """Create PointStatus from CLIST output."""
        # Determine point type
        if point_id.startswith('A'):
            point_type = 'Analog'
        elif point_id.startswith('P'):
            point_type = 'Digital'
        elif point_id.startswith('M'):
            point_type = 'Mapnet'
        else:
            point_type = 'Physical'

        # Parse status code
        state_type = {
            'C': 'Control',
            'T': 'Trouble',
            'U': 'Utility',
            'F': 'Fire',
            'S': 'Supervisory',
            'P': 'Priority2'
        }.get(status[0], 'Unknown')

        is_active = status[1] == '1'
        is_acknowledged = status[2] == '-'

        return cls(
            point_id=point_id,
            status=status,
            timestamp=datetime.now(),
            point_type=point_type,
            state_type=state_type,
            is_active=is_active,
            is_acknowledged=is_acknowledged
        )

@dataclass
class StatusChange:
    change_type: str  # 'NEW', 'CHANGED', 'CLEARED'
    previous_status: Optional[PointStatus]
    new_status: Optional[PointStatus]
    timestamp: datetime = datetime.now()