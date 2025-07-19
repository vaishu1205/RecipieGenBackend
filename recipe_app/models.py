from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class Recipe(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('dessert', 'Dessert'),
        ('appetizer', 'Appetizer'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    COOKING_TIME_CHOICES = [
        ('under_15', 'Under 15 min'),
        ('15_30', '15-30 min'),
        ('30_60', '30-60 min'),
        ('60_120', '1-2 hours'),
        ('over_120', '2+ hours'),
    ]

    # Basic Information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Recipe Details
    ingredients = models.TextField()  # JSON string of ingredients list
    instructions = models.TextField()  # JSON string of instructions list
    
    # Recipe Metadata
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, blank=True, null=True)
    cuisine_type = models.CharField(max_length=100, blank=True, null=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, blank=True, null=True)
    cooking_time = models.CharField(max_length=20, choices=COOKING_TIME_CHOICES, blank=True, null=True)
    
    # Servings and Timing
    servings = models.PositiveIntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    prep_time = models.PositiveIntegerField(null=True, blank=True, help_text="Prep time in minutes")
    cook_time = models.PositiveIntegerField(null=True, blank=True, help_text="Cook time in minutes")
    total_time = models.PositiveIntegerField(null=True, blank=True, help_text="Total time in minutes")
    
    # Dietary Information
    dietary_restrictions = models.TextField(blank=True, null=True)  # JSON string of restrictions list
    allergens = models.TextField(blank=True, null=True)  # JSON string of allergens
    
    # Nutrition Information
    calories_per_serving = models.PositiveIntegerField(null=True, blank=True)
    protein = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Protein in grams")
    carbs = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Carbs in grams")
    fat = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Fat in grams")
    fiber = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Fiber in grams")
    
    # Recipe Rating and Feedback
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    rating_count = models.PositiveIntegerField(default=0)
    
    # Additional Features
    tags = models.TextField(blank=True, null=True)  # JSON string of tags
    notes = models.TextField(blank=True, null=True)
    source_ingredients = models.TextField(blank=True, null=True)  # Original ingredients used in generation
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meal_type']),
            models.Index(fields=['cuisine_type']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['cooking_time']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_ingredients_list(self):
        """Return ingredients as a Python list"""
        try:
            return json.loads(self.ingredients) if self.ingredients else []
        except json.JSONDecodeError:
            # Fallback for old text-based ingredients
            return self.ingredients.split('\n') if self.ingredients else []
    
    def set_ingredients_list(self, ingredients_list):
        """Set ingredients from a Python list"""
        self.ingredients = json.dumps(ingredients_list)
    
    def get_instructions_list(self):
        """Return instructions as a Python list"""
        try:
            return json.loads(self.instructions) if self.instructions else []
        except json.JSONDecodeError:
            # Fallback for old text-based instructions
            return self.instructions.split('\n') if self.instructions else []
    
    def set_instructions_list(self, instructions_list):
        """Set instructions from a Python list"""
        self.instructions = json.dumps(instructions_list)
    
    def get_dietary_restrictions_list(self):
        """Return dietary restrictions as a Python list"""
        try:
            return json.loads(self.dietary_restrictions) if self.dietary_restrictions else []
        except json.JSONDecodeError:
            return self.dietary_restrictions.split(', ') if self.dietary_restrictions else []
    
    def set_dietary_restrictions_list(self, restrictions_list):
        """Set dietary restrictions from a Python list"""
        self.dietary_restrictions = json.dumps(restrictions_list)
    
    def get_tags_list(self):
        """Return tags as a Python list"""
        try:
            return json.loads(self.tags) if self.tags else []
        except json.JSONDecodeError:
            return []
    
    def set_tags_list(self, tags_list):
        """Set tags from a Python list"""
        self.tags = json.dumps(tags_list)
    
    def increment_view_count(self):
        """Increment the view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def update_rating(self, new_rating):
        """Update the average rating with a new rating"""
        if self.rating is None:
            self.rating = new_rating
            self.rating_count = 1
        else:
            total_rating = float(self.rating) * self.rating_count + new_rating
            self.rating_count += 1
            self.rating = total_rating / self.rating_count
        self.save(update_fields=['rating', 'rating_count'])
    
    @property
    def average_rating(self):
        """Get the average rating as a formatted string"""
        return f"{self.rating:.1f}" if self.rating else "No ratings"
    
    @property
    def total_time_formatted(self):
        """Get total time in a readable format"""
        if self.total_time:
            hours = self.total_time // 60
            minutes = self.total_time % 60
            if hours > 0:
                return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            return f"{minutes}m"
        return "Unknown"


class RecipeRating(models.Model):
    """Model to store individual recipe ratings"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True)  # For anonymous ratings
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['recipe', 'user_ip']  # Prevent duplicate ratings from same IP
    
    def __str__(self):
        return f"{self.recipe.title} - {self.rating} stars"


class RecipeGeneration(models.Model):
    """Model to track recipe generation requests and analytics"""
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE, related_name='generation_data')
    
    # Original request data
    requested_dietary_restrictions = models.TextField(blank=True, null=True)
    requested_cuisines = models.TextField(blank=True, null=True)
    requested_ingredients = models.TextField(blank=True, null=True)
    requested_meal_type = models.CharField(max_length=20, blank=True, null=True)
    requested_cooking_time = models.CharField(max_length=20, blank=True, null=True)
    requested_difficulty = models.CharField(max_length=20, blank=True, null=True)
    requested_servings = models.PositiveIntegerField(null=True, blank=True)
    
    # Generation metadata
    generation_time = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Time in seconds")
    ai_model_used = models.CharField(max_length=100, default="gemini-1.5-flash")
    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)
    
    # Success metrics
    generation_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Generation for {self.recipe.title}"