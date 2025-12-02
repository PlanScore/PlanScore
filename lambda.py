# Small zipfile functions
# ruff: noqa F401 (unused imports)
from planscore.preread import lambda_handler as preread
from planscore.postread_callback import lambda_handler_GET as postread_callback_GET
from planscore.postread_callback import lambda_handler_POST as postread_callback_POST
from planscore.upload_fields import lambda_handler as upload_fields
from planscore.authorizer import lambda_handler as authorizer
from planscore.get_states import lambda_handler as get_states
from planscore.get_model_versions import lambda_handler as get_model_versions
from planscore.api_clone import lambda_handler as api_clone

# Large docker functions
# from planscore.preread_followup import lambda_handler as preread_followup
# from planscore.postread_calculate import lambda_handler as postread_calculate
# from planscore.postread_intermediate import lambda_handler as postread_intermediate
# from planscore.api_upload import lambda_handler as api_upload
# from planscore.polygonize import lambda_handler as polygonize
