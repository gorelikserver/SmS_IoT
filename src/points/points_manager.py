import pandas as pd
from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime
import csv
import re
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PointInfo:
    point_id: str
    hardware_type: str
    point_type: str
    description: str
    location: str
    custom_fields: List[str]
    last_status: Optional[str] = None
    last_update: Optional[datetime] = None


class PointsManager:
    def __init__(self):
        self.points: Dict[str, PointInfo] = {}
        # Hebrew conversion mapping
        self.unicode_to_hebrew_map = {
            '\xa0': 'א', '\xa1': 'ב', '\xa2': 'ג', '\xa3': 'ד', '\xa4': 'ה', '\xa5': 'ו',
            '\xa6': 'ז', '\xa7': 'ח', '\xa8': 'ט', '\xa9': 'י', '\xab': 'כ', '\xac': 'ל',
            '\xae': 'מ', '\xb0': 'נ', '\xb1': 'ס', '\xb2': 'ע', '\xb4': 'פ', '\xb6': 'צ',
            '\xb7': 'ק', '\xb8': 'ר', '\xb9': 'ש', '\xba': 'ת', '\xaa': 'ך', '\xad': 'ם',
            '\xb3': 'ף', '\xb5': 'ץ', '\xaf': 'ן'
        }
        self.hebrew_to_unicode_map = {v: k for k, v in self.unicode_to_hebrew_map.items()}

    def convert_and_reverse_hebrew(self, text: str) -> str:
        """Convert and reverse Hebrew text properly"""
        try:
            # Pattern to match Mx-xxx format at start of string
            point_id_pattern = r'^(M\d+[-]\d+)'
            match = re.match(point_id_pattern, text)

            if not match:
                # If no point ID found, treat entire text as Hebrew
                converted = ''.join(self.unicode_to_hebrew_map.get(char, char)
                                    for char in text)[::-1]
                return converted

            point_id = match.group(1)  # Get the matched point ID
            hebrew_text = text[len(point_id):].strip()  # Get rest of text

            # Convert Hebrew characters and reverse
            converted_hebrew = ''.join(self.unicode_to_hebrew_map.get(char, char)
                                       for char in hebrew_text)[::-1]

            # Return in desired format: point_id followed by Hebrew
            return f"{point_id} {converted_hebrew}"

        except Exception as e:
            logger.error(f"Error converting Hebrew text '{text}': {e}")
            return text

    def load_points_file(self, file_path: str, encoding: str = 'windows-1252') -> None:
        """Load points from CSV file with Hebrew text handling"""
        try:
            df = pd.read_csv(file_path,
                             encoding=encoding,
                             header=None,
                             delimiter=',',
                             skipinitialspace=True)

            for _, row in df.iterrows():
                try:
                    fields = [str(field).strip() for field in row]

                    # Convert Hebrew text in description
                    description = self.convert_and_reverse_hebrew(fields[3])
                    logger.debug(f"Converted description: {description}")

                    point_info = PointInfo(
                        point_id=fields[0],
                        hardware_type=fields[1],
                        point_type=fields[2],
                        description=description,  # Converted Hebrew text
                        location=fields[4],
                        custom_fields=fields[5:],
                        last_status=None,
                        last_update=None
                    )

                    # Use point_id without trailing -0 as key
                    key = point_info.point_id.rsplit('-0', 1)[0]
                    self.points[key] = point_info

                except Exception as e:
                    logger.error(f"Error processing row {fields[0] if fields else 'unknown'}: {str(e)}")

            logger.info(f"Successfully loaded {len(self.points)} points")

        except Exception as e:
            raise Exception(f"Error loading points file: {str(e)}")

    def get_point_info(self, point_id: str) -> Optional[PointInfo]:
        """Get point info, handling the -0 suffix"""
        # Try exact match first
        point_info = self.points.get(point_id)
        if point_info:
            return point_info

        # Try without -0 suffix
        base_id = point_id.rsplit('-0', 1)[0]
        return self.points.get(base_id)

    def get_enriched_status(self, point_status: 'PointStatus') -> Dict:
        """Enrich a point status with description information"""
        point_info = self.get_point_info(point_status.point_id)
        if not point_info:
            logger.warning(f"No point information found for {point_status.point_id}")
            return point_status.__dict__

        return {
            **point_status.__dict__,
            'description': point_info.description,
            'location': point_info.location,
            'hardware_type': point_info.hardware_type,
            'configured_type': point_info.point_type,
            'custom_fields': point_info.custom_fields
        }

    def update_point_status(self, point_id: str, status: str) -> None:
        """Update status for a point"""
        point_info = self.get_point_info(point_id)
        if point_info:
            point_info.last_status = status
            point_info.last_update = datetime.now()
        else:
            logger.warning(f"Attempted to update status for unknown point: {point_id}")

    def export_points(self, file_path: str, encoding: str = 'utf-8') -> None:
        """Export points to CSV with status information"""
        try:
            with open(file_path, 'w', newline='', encoding=encoding) as f:
                writer = csv.writer(f)
                for point in self.points.values():
                    writer.writerow([
                        point.point_id,
                        point.hardware_type,
                        point.point_type,
                        point.description,
                        point.location,
                        point.last_status or 'N/A',
                        point.last_update.isoformat() if point.last_update else 'N/A',
                        *point.custom_fields
                    ])
        except Exception as e:
            raise Exception(f"Error exporting points: {str(e)}")