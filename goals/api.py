from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import date, timedelta
from .models import Goal, BodyMeasurement
from .serializers import GoalSerializer, BodyMeasurementSerializer

class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['goal_type', 'is_active', 'target_date']
    search_fields = ['notes']
    ordering_fields = ['created_at', 'updated_at', 'target_date']
    ordering = ['-created_at']

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a goal (deactivates others)"""
        goal = self.get_object()
        Goal.objects.filter(user=request.user, is_active=True).update(is_active=False)
        goal.is_active = True
        goal.save()
        return Response({'status': 'goal activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a goal"""
        goal = self.get_object()
        goal.is_active = False
        goal.save()
        return Response({'status': 'goal deactivated'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active goals"""
        active_goals = Goal.objects.filter(user=request.user, is_active=True)
        serializer = self.get_serializer(active_goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get goals grouped by type"""
        goal_type = request.query_params.get('type')
        if goal_type:
            goals = Goal.objects.filter(user=request.user, goal_type=goal_type)
        else:
            goals = Goal.objects.filter(user=request.user)
        
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get goals with upcoming target dates"""
        today = date.today()
        upcoming_goals = Goal.objects.filter(
            user=request.user,
            target_date__gte=today,
            is_active=True
        ).order_by('target_date')
        
        serializer = self.get_serializer(upcoming_goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue goals"""
        today = date.today()
        overdue_goals = Goal.objects.filter(
            user=request.user,
            target_date__lt=today,
            is_active=True
        ).order_by('target_date')
        
        serializer = self.get_serializer(overdue_goals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get progress summary for a goal"""
        goal = self.get_object()
        
        # Get related measurements
        measurements = BodyMeasurement.objects.filter(
            user=request.user,
            metric__in=['weight_kg', 'body_fat_percentage', 'muscle_mass_percentage']
        ).order_by('timestamp')
        
        if not measurements.exists():
            return Response({
                'goal': self.get_serializer(goal).data,
                'progress': 'No measurements recorded yet',
                'measurements_count': 0
            })
        
        latest_measurement = measurements.last()
        first_measurement = measurements.first()
        
        progress_data = {
            'goal': self.get_serializer(goal).data,
            'latest_measurement': BodyMeasurementSerializer(latest_measurement).data,
            'first_measurement': BodyMeasurementSerializer(first_measurement).data,
            'measurements_count': measurements.count(),
            'days_since_start': (latest_measurement.timestamp.date() - first_measurement.timestamp.date()).days
        }
        
        return Response(progress_data)

class BodyMeasurementViewSet(viewsets.ModelViewSet):
    queryset = BodyMeasurement.objects.all()
    serializer_class = BodyMeasurementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['metric', 'measurement_type']
    ordering_fields = ['timestamp', 'created_at', 'value']
    ordering = ['-timestamp']

    def get_queryset(self):
        return BodyMeasurement.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest measurement for each metric"""
        metrics = request.query_params.getlist('metrics', [
            'weight_kg', 'body_fat_percentage', 'muscle_mass_percentage'
        ])
        
        latest_measurements = []
        for metric in metrics:
            latest = BodyMeasurement.objects.filter(
                user=request.user,
                metric=metric
            ).order_by('-timestamp').first()
            
            if latest:
                latest_measurements.append(self.get_serializer(latest).data)
        
        return Response(latest_measurements)

    @action(detail=False, methods=['get'])
    def by_metric(self, request):
        """Get all measurements for a specific metric"""
        metric = request.query_params.get('metric')
        if not metric:
            return Response(
                {'error': 'metric parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        measurements = BodyMeasurement.objects.filter(
            user=request.user,
            metric=metric
        ).order_by('-timestamp')
        
        serializer = self.get_serializer(measurements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get measurement trends over time"""
        metric = request.query_params.get('metric', 'weight_kg')
        days = int(request.query_params.get('days', 30))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        measurements = BodyMeasurement.objects.filter(
            user=request.user,
            metric=metric,
            timestamp__date__range=[start_date, end_date]
        ).order_by('timestamp')
        
        trend_data = []
        for measurement in measurements:
            trend_data.append({
                'date': measurement.timestamp.date(),
                'value': measurement.value,
                'measurement_type': measurement.measurement_type
            })
        
        return Response({
            'metric': metric,
            'period_days': days,
            'start_date': start_date,
            'end_date': end_date,
            'measurements': trend_data,
            'count': len(trend_data)
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get measurement summary for all metrics"""
        metrics = [
            'weight_kg', 'waist_cm', 'hip_cm', 'neck_cm',
            'body_fat_percentage', 'muscle_mass_percentage', 'bmi_value'
        ]
        
        summary = {}
        for metric in metrics:
            latest = BodyMeasurement.objects.filter(
                user=request.user,
                metric=metric
            ).order_by('-timestamp').first()
            
            if latest:
                summary[metric] = {
                    'latest_value': latest.value,
                    'latest_date': latest.timestamp.date(),
                    'measurement_type': latest.measurement_type
                }
        
        return Response(summary)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple measurements at once"""
        measurements_data = request.data.get('measurements', [])
        created_measurements = []
        
        for measurement_data in measurements_data:
            measurement_data['user'] = request.user.id
            serializer = self.get_serializer(data=measurement_data)
            if serializer.is_valid():
                measurement = serializer.save()
                created_measurements.append(measurement)
            else:
                return Response(
                    {'error': f'Invalid measurement data: {serializer.errors}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            self.get_serializer(created_measurements, many=True).data,
            status=status.HTTP_201_CREATED
        )
