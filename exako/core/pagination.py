from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal

Page = CustomizedPage[
    Page,
    UseIncludeTotal(True),
]
