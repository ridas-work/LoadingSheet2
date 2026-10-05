from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsBatchClerkOrAdmin

from .models import Batch, BatchProduct
from .serializers import BatchProductSerializer, BatchSerializer


class BatchProductListView(generics.ListAPIView):
    permission_classes = [IsBatchClerkOrAdmin]
    serializer_class = BatchProductSerializer

    def get_queryset(self):
        return BatchProduct.objects.filter(is_active=True)


class BatchListCreateView(APIView):
    permission_classes = [IsBatchClerkOrAdmin]

    def get_queryset(self, request):
        qs = Batch.objects.select_related("batch_product", "created_by")
        user = request.user
        if user.role == "batch_clerk":
            qs = qs.filter(created_by=user)

        status_filter = request.query_params.get("status", "active")
        if status_filter == "active":
            qs = qs.filter(is_closed=False)
        elif status_filter == "closed":
            qs = qs.filter(is_closed=True)

        purpose = request.query_params.get("purpose")
        if purpose in (Batch.Purpose.REGULAR, Batch.Purpose.SAMPLE):
            qs = qs.filter(purpose=purpose)

        search = (request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(batch_number__icontains=search)
                | Q(batch_product__name__icontains=search)
            )
        return qs

    def get(self, request):
        qs = self.get_queryset(request)
        return Response(BatchSerializer(qs, many=True).data)

    def post(self, request):
        serializer = BatchSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        return Response(
            BatchSerializer(batch).data, status=status.HTTP_201_CREATED
        )


class BatchDetailView(APIView):
    permission_classes = [IsBatchClerkOrAdmin]

    def get_object(self, request, pk):
        qs = Batch.objects.select_related("batch_product", "created_by")
        if request.user.role == "batch_clerk":
            qs = qs.filter(created_by=request.user)
        return qs.filter(pk=pk).first()

    def get(self, request, pk):
        batch = self.get_object(request, pk)
        if batch is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(BatchSerializer(batch).data)

    def put(self, request, pk):
        batch = self.get_object(request, pk)
        if batch is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BatchSerializer(
            batch, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        saved = serializer.save()
        return Response(BatchSerializer(saved).data)

    def delete(self, request, pk):
        batch = self.get_object(request, pk)
        if batch is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        batch.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
