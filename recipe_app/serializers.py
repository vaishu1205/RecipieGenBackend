# Recipe App Serializers
# recipe_generator/serializers.py
from rest_framework import serializers
from .models import Recipe, RecipeRating, RecipeGeneration
import json

class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for Recipe model instances with enhanced features.
    """
    ingredients = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    dietary_restrictions = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    nutrition = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    total_time_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'description', 'ingredients', 'instructions',
            'meal_type', 'cuisine_type', 'difficulty', 'cooking_time',
            'servings', 'prep_time', 'cook_time', 'total_time', 'total_time_formatted',
            'dietary_restrictions', 'allergens', 'calories_per_serving',
            'protein', 'carbs', 'fat', 'fiber', 'rating', 'rating_count',
            'average_rating', 'tags', 'notes', 'created_at', 'updated_at',
            'view_count', 'is_featured', 'nutrition'
        ]
    
    def get_ingredients(self, obj):
        """Return ingredients as a list"""
        return obj.get_ingredients_list()
    
    def get_instructions(self, obj):
        """Return instructions as a list"""
        return obj.get_instructions_list()
    
    def get_dietary_restrictions(self, obj):
        """Return dietary restrictions as a list"""
        return obj.get_dietary_restrictions_list()
    
    def get_tags(self, obj):
        """Return tags as a list"""
        return obj.get_tags_list()
    
    def get_nutrition(self, obj):
        """Return nutrition information as a structured object"""
        nutrition = {}
        if obj.calories_per_serving:
            nutrition['calories'] = obj.calories_per_serving
        if obj.protein:
            nutrition['protein'] = f"{obj.protein}g"
        if obj.carbs:
            nutrition['carbs'] = f"{obj.carbs}g"
        if obj.fat:
            nutrition['fat'] = f"{obj.fat}g"
        if obj.fiber:
            nutrition['fiber'] = f"{obj.fiber}g"
        return nutrition if nutrition else None


class RecipeListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for recipe lists.
    """
    average_rating = serializers.ReadOnlyField()
    total_time_formatted = serializers.ReadOnlyField()
    dietary_restrictions = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'description', 'meal_type', 'cuisine_type',
            'difficulty', 'cooking_time', 'servings', 'total_time_formatted',
            'dietary_restrictions', 'rating', 'average_rating', 'view_count',
            'is_featured', 'created_at'
        ]
    
    def get_dietary_restrictions(self, obj):
        """Return dietary restrictions as a list"""
        return obj.get_dietary_restrictions_list()


class RecipeRequestSerializer(serializers.Serializer):
    """
    Serializer for recipe generation requests with enhanced features.
    """
    # Core ingredients and preferences
    dietary_restrictions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text="List of dietary restrictions (e.g., ['Vegetarian', 'Gluten-Free'])"
    )
    preferred_cuisines = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text="List of preferred cuisines (e.g., ['Italian', 'Mexican'])"
    )
    available_ingredients = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        help_text="List of available ingredients (e.g., ['Chicken', 'Rice', 'Tomatoes'])"
    )
    
    # Recipe specifications
    meal_type = serializers.ChoiceField(
        choices=Recipe.MEAL_TYPE_CHOICES,
        required=False,
        allow_blank=True,
        help_text="Type of meal (breakfast, lunch, dinner, etc.)"
    )
    cooking_time = serializers.ChoiceField(
        choices=Recipe.COOKING_TIME_CHOICES,
        required=False,
        allow_blank=True,
        help_text="Preferred cooking time"
    )
    difficulty = serializers.ChoiceField(
        choices=Recipe.DIFFICULTY_CHOICES,
        required=False,
        allow_blank=True,
        help_text="Cooking difficulty level"
    )
    servings = serializers.IntegerField(
        min_value=1,
        max_value=20,
        default=4,
        help_text="Number of servings"
    )
    
    # Optional preferences
    exclude_ingredients = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text="Ingredients to avoid"
    )
    flavor_profile = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Desired flavor profile (e.g., 'spicy', 'mild', 'sweet')"
    )
    cooking_method = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Preferred cooking method (e.g., 'baked', 'grilled', 'one-pot')"
    )
    special_requests = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Any special requests or notes"
    )
    
    def validate_available_ingredients(self, value):
        """Validate that at least one ingredient is provided"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one ingredient must be provided.")
        return value
    
    def validate_servings(self, value):
        """Validate servings range"""
        if value < 1 or value > 20:
            raise serializers.ValidationError("Servings must be between 1 and 20.")
        return value


class RecipeRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for recipe ratings.
    """
    class Meta:
        model = RecipeRating
        fields = ['rating', 'comment', 'created_at']
        read_only_fields = ['created_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating recipes manually (admin/staff use).
    """
    ingredients = serializers.ListField(
        child=serializers.CharField(max_length=200),
        help_text="List of ingredients"
    )
    instructions = serializers.ListField(
        child=serializers.CharField(max_length=1000),
        help_text="List of cooking instructions"
    )
    dietary_restrictions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text="List of dietary restrictions"
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        help_text="List of tags"
    )
    
    class Meta:
        model = Recipe
        fields = [
            'title', 'description', 'ingredients', 'instructions',
            'meal_type', 'cuisine_type', 'difficulty', 'cooking_time',
            'servings', 'prep_time', 'cook_time', 'dietary_restrictions',
            'allergens', 'calories_per_serving', 'protein', 'carbs',
            'fat', 'fiber', 'tags', 'notes'
        ]
    
    def create(self, validated_data):
        """Create recipe with list-based fields"""
        ingredients = validated_data.pop('ingredients', [])
        instructions = validated_data.pop('instructions', [])
        dietary_restrictions = validated_data.pop('dietary_restrictions', [])
        tags = validated_data.pop('tags', [])
        
        recipe = Recipe.objects.create(**validated_data)
        recipe.set_ingredients_list(ingredients)
        recipe.set_instructions_list(instructions)
        recipe.set_dietary_restrictions_list(dietary_restrictions)
        recipe.set_tags_list(tags)
        recipe.save()
        
        return recipe


class RecipeSearchSerializer(serializers.Serializer):
    """
    Serializer for recipe search parameters.
    """
    query = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Search query for recipe title or ingredients"
    )
    meal_type = serializers.ChoiceField(
        choices=Recipe.MEAL_TYPE_CHOICES,
        required=False,
        allow_blank=True
    )
    cuisine_type = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )
    difficulty = serializers.ChoiceField(
        choices=Recipe.DIFFICULTY_CHOICES,
        required=False,
        allow_blank=True
    )
    cooking_time = serializers.ChoiceField(
        choices=Recipe.COOKING_TIME_CHOICES,
        required=False,
        allow_blank=True
    )
    dietary_restrictions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list
    )
    min_rating = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        min_value=0,
        max_value=5,
        required=False
    )
    max_servings = serializers.IntegerField(
        min_value=1,
        max_value=20,
        required=False
    )
    ordering = serializers.ChoiceField(
        choices=[
            ('created_at', 'Newest First'),
            ('-created_at', 'Oldest First'),
            ('rating', 'Lowest Rated'),
            ('-rating', 'Highest Rated'),
            ('view_count', 'Least Popular'),
            ('-view_count', 'Most Popular'),
            ('title', 'A-Z'),
            ('-title', 'Z-A'),
        ],
        default='-created_at',
        required=False
    )