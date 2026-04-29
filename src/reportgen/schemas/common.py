from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BeforeValidator

NonEmptyString = Annotated[str, BeforeValidator(lambda value: value.strip() if isinstance(value, str) else value)]

ISODate = date
UTCTimestamp = datetime
ReportId = UUID
RunId = UUID
