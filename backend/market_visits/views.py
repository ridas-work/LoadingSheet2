from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import CanMarketVisit

from .columns import MARKET_VISIT_COLUMNS, grouped_columns
from .models import MarketVisit
from .serializers import (
    MarketVisitListSerializer,
    MarketVisitSerializer,
    MarketVisitWriteSerializer,
)


def user_visits(user):
    return (
        MarketVisit.objects.filter(created_by=user)
        .select_related("created_by")
        .prefetch_related("stores")
    )


class MarketVisitColumnsView(APIView):
    permission_classes = [CanMarketVisit]

    def get(self, request):
        return Response(
            {
                "columns": MARKET_VISIT_COLUMNS,
                "groups": grouped_columns(),
            }
        )


class MarketVisitListCreateView(APIView):
    permission_classes = [CanMarketVisit]

    def get(self, request):
        qs = user_visits(request.user)
        status_filter = request.query_params.get("status")
        if status_filter in (
            MarketVisit.Status.IN_PROCESS,
            MarketVisit.Status.SUBMITTED,
        ):
            qs = qs.filter(status=status_filter)
        visits = [v for v in qs if v.stores.exists()]
        return Response(MarketVisitListSerializer(visits, many=True).data)

    def post(self, request):
        serializer = MarketVisitWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data["stores"]:
            return Response(
                {"detail": "Empty market visit was not saved.", "deleted": True},
                status=status.HTTP_200_OK,
            )
        visit = serializer.save()
        return Response(
            MarketVisitSerializer(visit).data, status=status.HTTP_201_CREATED
        )


class MarketVisitDetailView(APIView):
    permission_classes = [CanMarketVisit]

    def get_object(self, request, pk):
        return user_visits(request.user).filter(pk=pk).first()

    def get(self, request, pk):
        visit = self.get_object(request, pk)
        if visit is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(MarketVisitSerializer(visit).data)

    def put(self, request, pk):
        visit = self.get_object(request, pk)
        if visit is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if visit.status == MarketVisit.Status.SUBMITTED:
            return Response(
                {"detail": "Submitted market visits cannot be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MarketVisitWriteSerializer(
            visit, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data["stores"]:
            visit.delete()
            return Response(
                {"detail": "Empty market visit removed.", "deleted": True},
                status=status.HTTP_200_OK,
            )
        saved = serializer.save()
        return Response(MarketVisitSerializer(saved).data)

    def delete(self, request, pk):
        visit = self.get_object(request, pk)
        if visit is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if visit.status == MarketVisit.Status.SUBMITTED:
            return Response(
                {"detail": "Submitted market visits cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        visit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
