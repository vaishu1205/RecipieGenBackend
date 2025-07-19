# recipe_generator/urls.py
from django.urls import path
from .views import (
    RecipeGeneratorView,
    RecipeListView,
    RecipeDetailView,
    RecipeRatingView,
    PopularRecipesView,
    FeaturedRecipesView,
    RecipeStatsView,
    recipe_reviews,
    recipe_suggestions
)

app_name = 'recipe_app'

urlpatterns = [
    # Core recipe functionality
    path('generate-recipe/', RecipeGeneratorView.as_view(), name='generate_recipe'),
    path('recipes/', RecipeListView.as_view(), name='recipe_list'),
    path('recipes/<int:pk>/', RecipeDetailView.as_view(), name='recipe_detail'),
    
    # Recipe interactions
    path('recipes/<int:recipe_id>/rate/', RecipeRatingView.as_view(), name='rate_recipe'),
    path('recipes/<int:recipe_id>/reviews/', recipe_reviews, name='recipe_reviews'),
    # Discovery endpoints
    path('recipes/popular/', PopularRecipesView.as_view(), name='popular_recipes'),
    path('recipes/featured/', FeaturedRecipesView.as_view(), name='featured_recipes'),
    path('recipes/suggestions/', recipe_suggestions, name='recipe_suggestions'),
    
    # Analytics
    path('stats/', RecipeStatsView.as_view(), name='recipe_stats'),
]