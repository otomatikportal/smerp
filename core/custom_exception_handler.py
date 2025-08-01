import logging
import traceback
from collections import OrderedDict
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.conf import settings

logger = logging.getLogger(__name__)


def flatten_error_details(detail, key_prefix=''):
    """
    Recursively flattens DRF ValidationError details into a list of strings.
    """
    errors = []
    if isinstance(detail, dict):
        for key, value in detail.items():
            new_prefix = f"{key_prefix}.{key}" if key_prefix else key
            errors.extend(flatten_error_details(value, new_prefix))
    elif isinstance(detail, list):
        for item in detail:
            errors.extend(flatten_error_details(item, key_prefix))
    else:
        errors.append(str(detail))
    return errors


def format_errors(detail):
    """
    Formats the error details into a simplified dict structure.
    """
    if isinstance(detail, dict):
        return {
            key: format_errors(value)
            for key, value in detail.items()
        }
    elif isinstance(detail, list):
        # Handle list of dicts (e.g. nested serializers with many=True)
        if all(isinstance(item, dict) for item in detail):
            return [format_errors(item) for item in detail]
        else:
            return [str(item) for item in detail]
    else:
        return [str(detail)]


def extract_non_field_errors(detail):
    """
    Extracts all non-field error messages if present.
    """
    errors = []
    if isinstance(detail, dict) and 'non_field_errors' in detail:
        non_field_errors = detail['non_field_errors']
        if isinstance(non_field_errors, list):
            errors.extend([str(e) for e in non_field_errors])
    return errors


def extract_detail_error_message(detail):
    """
    Extract message from detail-based errors (pagination, permissions, etc.)
    """
    if isinstance(detail, dict) and 'detail' in detail:
        detail_errors = detail['detail']
        if isinstance(detail_errors, list) and len(detail_errors) > 0:
            return str(detail_errors[0])
    return None


def custom_exception_handler(exc, context):
    # Get the default response first
    response = exception_handler(exc, context)

    # Handle validation errors (400 series)
    if response is not None:
        original_data = response.data

        # Format the error details
        formatted_details = format_errors(original_data)

        # Try to get specific error messages in order of priority:
        
        # 1. Non-field errors (business logic)
        non_field_errors = extract_non_field_errors(original_data)
        if non_field_errors:
            if len(non_field_errors) > 3:
                message = "; ".join(non_field_errors[:3]) + f" ... ve {len(non_field_errors) - 3} daha fazla hata."
            else:
                message = "; ".join(non_field_errors)
        
        # 2. Detail errors (pagination, permissions, etc.)
        elif isinstance(original_data, dict) and 'detail' in original_data:
            detail_msg = str(original_data['detail'])
            # You can translate common messages here
            message = detail_msg
        
        # 3. Fallback for field errors
        else:
            message = "Hatalı giriş, alanları düzeltiniz."

        custom_response = OrderedDict([
            ('status', 'error'),
            ('message', message),
            ('details', formatted_details),
        ])

        response.data = custom_response

    # Handle server errors (500 series) - unchanged
    else:
        logger.error(f"Internal Server Error: {exc}", exc_info=True)
        
        error_response = {
            "status": "error",
            "message": "Server Hatası!: 500",
            "details": {}
        }
        
        if settings.DEBUG:
            error_response["details"] = {
                "traceback": traceback.format_exc(),
                "exception": str(exc),
                "view": str(context['view']) if 'view' in context else None
            }
        
        response = Response(error_response, status=500)

    return response