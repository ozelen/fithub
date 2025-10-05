from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Diet, Meal, Ingredient, Category, MealRecord, MealPreference, MealIngredient
from .serializers import (
    DietSerializer, MealSerializer, IngredientSerializer, CategorySerializer,
    MealRecordSerializer, MealPreferenceSerializer, MealIngredientSerializer,
    IngredientSearchSerializer
)

class DietViewSet(viewsets.ModelViewSet):
    queryset = Diet.objects.all()
    serializer_class = DietSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'start_date']
    ordering = ['-created_at']

    def get_queryset(self):
        return Diet.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a diet (deactivates others)"""
        diet = self.get_object()
        Diet.objects.filter(user=request.user, is_active=True).update(is_active=False)
        diet.is_active = True
        diet.save()
        return Response({'status': 'diet activated'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get the currently active diet"""
        try:
            active_diet = Diet.objects.get(user=request.user, is_active=True)
            serializer = self.get_serializer(active_diet)
            return Response(serializer.data)
        except Diet.DoesNotExist:
            return Response({'error': 'No active diet found'}, status=status.HTTP_404_NOT_FOUND)

class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['diet', 'meal_type', 'is_scheduled', 'recurrence_type']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'start_date', 'start_time']
    ordering = ['-created_at']

    def get_queryset(self):
        return Meal.objects.filter(diet__user=self.request.user)

    @action(detail=True, methods=['get'])
    def ingredients(self, request, pk=None):
        """Get all ingredients for a meal"""
        meal = self.get_object()
        ingredients = meal.mealingredient_set.all()
        serializer = MealIngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_ingredient(self, request, pk=None):
        """Add an ingredient to a meal"""
        meal = self.get_object()
        data = request.data.copy()
        data['meal'] = meal.id
        serializer = MealIngredientSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def nutrition_summary(self, request, pk=None):
        """Get nutritional summary for a meal"""
        meal = self.get_object()
        total_calories = meal.get_total_calories()
        # Calculate other macros
        total_proteins = sum(
            (mi.quantity / 100) * mi.ingredient.proteins 
            for mi in meal.mealingredient_set.all()
        )
        total_fats = sum(
            (mi.quantity / 100) * mi.ingredient.fats 
            for mi in meal.mealingredient_set.all()
        )
        total_carbs = sum(
            (mi.quantity / 100) * mi.ingredient.carbs 
            for mi in meal.mealingredient_set.all()
        )
        
        return Response({
            'total_calories': total_calories,
            'total_proteins': total_proteins,
            'total_fats': total_fats,
            'total_carbs': total_carbs,
            'ingredient_count': meal.mealingredient_set.count()
        })

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_personal']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'calories', 'proteins', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        # Show both public ingredients and user's personal ingredients
        return Ingredient.objects.filter(
            Q(is_personal=False) | Q(created_by=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, is_personal=True)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search ingredients with autocomplete"""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response({'error': 'Query must be at least 2 characters'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        ingredients = Ingredient.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:10]
        serializer = IngredientSearchSerializer(ingredients, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def personal(self, request):
        """Get user's personal ingredients"""
        ingredients = Ingredient.objects.filter(
            created_by=request.user, is_personal=True
        )
        serializer = self.get_serializer(ingredients, many=True)
        return Response(serializer.data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Category.objects.all()

class MealRecordViewSet(viewsets.ModelViewSet):
    queryset = MealRecord.objects.all()
    serializer_class = MealRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['meal', 'timestamp']
    search_fields = ['meal_name', 'feedback']
    ordering_fields = ['timestamp', 'created_at']
    ordering = ['-timestamp']

    def get_queryset(self):
        return MealRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's meal records"""
        from django.utils import timezone
        today = timezone.now().date()
        records = MealRecord.objects.filter(
            user=request.user,
            timestamp__date=today
        )
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def nutrition_summary(self, request):
        """Get nutritional summary for a date range"""
        from django.utils import timezone
        from datetime import timedelta
        
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        records = MealRecord.objects.filter(
            user=request.user,
            timestamp__date__range=[start_date, end_date]
        )
        
        total_calories = sum(record.get_total_calories() for record in records)
        total_proteins = sum(record.get_total_proteins() for record in records)
        total_fats = sum(record.get_total_fats() for record in records)
        total_carbs = sum(record.get_total_carbs() for record in records)
        
        return Response({
            'period_days': days,
            'start_date': start_date,
            'end_date': end_date,
            'total_calories': total_calories,
            'total_proteins': total_proteins,
            'total_fats': total_fats,
            'total_carbs': total_carbs,
            'record_count': records.count()
        })

class MealPreferenceViewSet(viewsets.ModelViewSet):
    queryset = MealPreference.objects.all()
    serializer_class = MealPreferenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['preference_type', 'ingredient']
    search_fields = ['ingredient__name', 'description']
    ordering_fields = ['created_at', 'preference_type']
    ordering = ['-created_at']

    def get_queryset(self):
        return MealPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get preferences grouped by type"""
        preference_type = request.query_params.get('type')
        if preference_type:
            preferences = MealPreference.objects.filter(
                user=request.user,
                preference_type=preference_type
            )
        else:
            preferences = MealPreference.objects.filter(user=request.user)
        
        serializer = self.get_serializer(preferences, many=True)
        return Response(serializer.data)

class MealIngredientViewSet(viewsets.ModelViewSet):
    queryset = MealIngredient.objects.all()
    serializer_class = MealIngredientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['meal', 'ingredient']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']

    def get_queryset(self):
        return MealIngredient.objects.filter(meal__diet__user=self.request.user)