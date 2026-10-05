from rest_framework import permissions


class IsOrderClerk(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "order_clerk"
        )


class IsOrderClerkOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("order_clerk", "admin")
        )


class CanMarketVisit(permissions.BasePermission):
    message = "Market Visit access is restricted."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "can_market_visit", False)
        )
