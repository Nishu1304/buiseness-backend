class CurrentTenantMiddleware:
    """
    Extract tenant from logged in user and attach it to request
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        user = getattr(request, 'user', None)

        if user and user.is_authenticated:
            # Safely get tenant attribute, handle cases where it doesn't exist or is None
            request.tenant = getattr(user, 'tenant', None)
        else:
            request.tenant = None

        return self.get_response(request)

        