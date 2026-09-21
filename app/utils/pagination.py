"""
Pagination utility - reusable across all routers
Handles page/page_size validation and query offset/limit
"""


class PaginationParams:
    """
    Helper class for pagination.

    Usage:
        pagination = PaginationParams(page=1, page_size=50)
        results = pagination.apply(query).all()
    """

    def __init__(self, page: int = 1, page_size: int = 50):
        # Validate and adjust page
        self.page = max(1, page) if page else 1

        # Validate and adjust page_size
        self.page_size = page_size if page_size else 50
        self.page_size = max(1, self.page_size)   # Min 1
        self.page_size = min(self.page_size, 100)  # Max 100

        # Calculate offset
        self.offset = (self.page - 1) * self.page_size

    def apply(self, query):
        """Apply pagination to a SQLAlchemy query."""
        return query.offset(self.offset).limit(self.page_size)

    def get_params(self):
        """Return pagination parameters as dict."""
        return {
            "page": self.page,
            "page_size": self.page_size,
            "offset": self.offset
        }
