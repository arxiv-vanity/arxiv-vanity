from django.http import Http404
from rest_framework import generics, mixins, status
from rest_framework.response import Response
from .models import Render
from .serializers import RenderSerializer


class RenderDetail(mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Render.objects.all()
    serializer_class = RenderSerializer

    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            serializer = self.get_serializer(data=self.get_lookup_kwargs())
            serializer.is_valid(raise_exception=True)
            render = serializer.save()
            render.delay()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        instance.update_state()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_lookup_kwargs(self):
        return {
            "source_type": self.request.GET["source_type"],
            "source_id": self.request.GET["source_id"],
        }

    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        queryset = queryset.filter(**self.get_lookup_kwargs())
        try:
            obj = queryset.latest()
        except Render.DoesNotExist:
            raise Http404
        else:
            self.check_object_permissions(self.request, obj)
            return obj
