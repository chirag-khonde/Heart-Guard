"""HeartGuard data module.

Provides dataset loading, validation, preprocessing, and quality
reporting for the Cleveland and Framingham heart disease datasets.
"""

from src.data.loader import (
    load_cleveland_dataset,
    load_csv,
    load_framingham_dataset,
    prepare_cleveland_dataset,
    prepare_framingham_dataset,
    validate_dataset_exists,
)
from src.data.preprocessing import (
    create_preprocessor,
    fit_preprocessor,
    get_duplicate_report,
    get_feature_names,
    get_missing_value_report,
    split_dataset,
    transform_data,
)

# Note: src.data.pipeline and src.data.quality are importable directly
# but not re-exported here to avoid circular imports.
# Use:  from src.data.pipeline import prepare_cleveland_pipeline
