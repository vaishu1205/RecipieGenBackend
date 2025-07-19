import json
import time
import re
import google.generativeai as genai
from django.conf import settings
from django.db import models
from django.db.models import Q, Avg, Sum, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from .models import Recipe, RecipeRating, RecipeGeneration
from .serializers import (
    RecipeSerializer, RecipeListSerializer, RecipeRequestSerializer,
    RecipeRatingSerializer, RecipeSearchSerializer
)

class RecipePagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50

class RecipeGeneratorView(APIView):
    """
    Enhanced API endpoint for generating personalized recipes using Gemini AI.
    """
    
    def post(self, request):
        start_time = time.time()
        serializer = RecipeRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        data = serializer.validated_data
        dietary_restrictions = data.get('dietary_restrictions', [])
        preferred_cuisines = data.get('preferred_cuisines', [])
        available_ingredients = data.get('available_ingredients', [])
        meal_type = data.get('meal_type', '')
        cooking_time = data.get('cooking_time', '')
        difficulty = data.get('difficulty', '')
        servings = data.get('servings', 4)
        exclude_ingredients = data.get('exclude_ingredients', [])
        flavor_profile = data.get('flavor_profile', '')
        cooking_method = data.get('cooking_method', '')
        special_requests = data.get('special_requests', '')
        
        # Configure Gemini API
        API_KEY = "AIzaSyCTSyuImJ2J_alyHPbQMyfSsLnOaWvIFvU"
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create enhanced prompt for Gemini
        prompt = self.create_enhanced_recipe_prompt(
            dietary_restrictions, preferred_cuisines, available_ingredients,
            meal_type, cooking_time, difficulty, servings, exclude_ingredients,
            flavor_profile, cooking_method, special_requests
        )
        
        try:
            # Generate recipe from Gemini
            response = model.generate_content(prompt)
            generation_time = time.time() - start_time
            
            # Extract recipe data from Gemini response
            recipe_data = self.extract_enhanced_recipe_data(
                response.text, data
            )
            
            # Create recipe instance
            recipe = Recipe.objects.create(
                title=recipe_data['title'],
                description=recipe_data['description'],
                meal_type=meal_type,
                cuisine_type=', '.join(preferred_cuisines) if preferred_cuisines else None,
                difficulty=difficulty,
                cooking_time=cooking_time,
                servings=servings,
                prep_time=recipe_data.get('prep_time'),
                cook_time=recipe_data.get('cook_time'),
                total_time=recipe_data.get('total_time'),
                calories_per_serving=recipe_data.get('calories'),
                protein=recipe_data.get('protein'),
                carbs=recipe_data.get('carbs'),
                fat=recipe_data.get('fat'),
                fiber=recipe_data.get('fiber'),
                notes=recipe_data.get('notes'),
                source_ingredients=json.dumps(available_ingredients)
            )
            
            # Set list-based fields
            recipe.set_ingredients_list(recipe_data['ingredients'])
            recipe.set_instructions_list(recipe_data['instructions'])
            recipe.set_dietary_restrictions_list(dietary_restrictions)
            recipe.set_tags_list(recipe_data.get('tags', []))
            recipe.save()
            
            # Create generation tracking record
            RecipeGeneration.objects.create(
                recipe=recipe,
                requested_dietary_restrictions=json.dumps(dietary_restrictions),
                requested_cuisines=json.dumps(preferred_cuisines),
                requested_ingredients=json.dumps(available_ingredients),
                requested_meal_type=meal_type,
                requested_cooking_time=cooking_time,
                requested_difficulty=difficulty,
                requested_servings=servings,
                generation_time=generation_time,
                ai_model_used="gemini-1.5-flash",
                generation_successful=True
            )
            
            # Serialize and return the recipe
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print("EXCEPTION:", str(e))
            
            # Log failed generation
            RecipeGeneration.objects.create(
                requested_dietary_restrictions=json.dumps(dietary_restrictions),
                requested_cuisines=json.dumps(preferred_cuisines),
                requested_ingredients=json.dumps(available_ingredients),
                requested_meal_type=meal_type,
                requested_cooking_time=cooking_time,
                requested_difficulty=difficulty,
                requested_servings=servings,
                generation_time=time.time() - start_time,
                ai_model_used="gemini-1.5-flash",
                generation_successful=False,
                error_message=str(e)
            )
            
            return Response(
                {'error': f'Failed to generate recipe: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create_enhanced_recipe_prompt(self, dietary_restrictions, preferred_cuisines, 
                                    available_ingredients, meal_type, cooking_time, 
                                    difficulty, servings, exclude_ingredients, 
                                    flavor_profile, cooking_method, special_requests):
        """
        Create an enhanced structured prompt for Gemini to generate a recipe.
        """
        dietary_str = ', '.join(dietary_restrictions) if dietary_restrictions else 'none'
        cuisine_str = ', '.join(preferred_cuisines) if preferred_cuisines else 'any'
        ingredients_str = ', '.join(available_ingredients)
        exclude_str = ', '.join(exclude_ingredients) if exclude_ingredients else 'none'
        
        prompt = f"""
        Create a unique, delicious, and well-structured recipe with the following requirements:
        
        REQUIREMENTS:
        - Available Ingredients: {ingredients_str}
        - Dietary Restrictions: {dietary_str}
        - Preferred Cuisines: {cuisine_str}
        - Meal Type: {meal_type or 'any'}
        - Cooking Time: {cooking_time or 'flexible'}
        - Difficulty Level: {difficulty or 'any'}
        - Number of Servings: {servings}
        - Exclude Ingredients: {exclude_str}
        - Flavor Profile: {flavor_profile or 'balanced'}
        - Cooking Method: {cooking_method or 'any'}
        - Special Requests: {special_requests or 'none'}
        
        Please format the recipe EXACTLY as follows:
        
        TITLE: [Creative and appetizing recipe title]
        
        DESCRIPTION: [2-3 sentence description of the dish, highlighting key flavors and appeal]
        
        PREP_TIME: [Number only, in minutes]
        COOK_TIME: [Number only, in minutes]
        TOTAL_TIME: [Number only, in minutes]
        
        INGREDIENTS:
        - [Ingredient 1 with specific measurements]
        - [Ingredient 2 with specific measurements]
        - [Continue for all ingredients...]
        
        INSTRUCTIONS:
        1. [Detailed step 1]
        2. [Detailed step 2]
        3. [Continue for all steps...]
        
        NUTRITION_INFO:
        Calories: [Number per serving]
        Protein: [Number in grams]
        Carbs: [Number in grams]
        Fat: [Number in grams]
        Fiber: [Number in grams]
        
        TAGS: [Comma-separated list of relevant tags like "quick", "healthy", "comfort food", etc.]
        
        NOTES: [Any helpful tips, variations, or storage instructions]
        
        Make sure the recipe is practical, uses the available ingredients creatively, and respects all dietary restrictions.
        """
        
        return prompt
    
    def extract_enhanced_recipe_data(self, gemini_response, request_data):
        """
        Extract structured recipe data from Gemini's enhanced response.
        """
        # Default values
        recipe_data = {
            'title': 'Personalized Recipe',
            'description': 'A delicious recipe created just for you',
            'ingredients': [],
            'instructions': [],
            'prep_time': None,
            'cook_time': None,
            'total_time': None,
            'calories': None,
            'protein': None,
            'carbs': None,
            'fat': None,
            'fiber': None,
            'tags': [],
            'notes': ''
        }
        
        try:
            # Extract title
            if "TITLE:" in gemini_response:
                title_line = gemini_response.split("TITLE:")[1].split("\n")[0].strip()
                recipe_data['title'] = title_line
            
            # Extract description
            if "DESCRIPTION:" in gemini_response:
                desc_section = gemini_response.split("DESCRIPTION:")[1]
                if "PREP_TIME:" in desc_section:
                    desc_section = desc_section.split("PREP_TIME:")[0]
                recipe_data['description'] = desc_section.strip()
            
            # Extract timing
            if "PREP_TIME:" in gemini_response:
                prep_match = re.search(r'PREP_TIME:\s*(\d+)', gemini_response)
                if prep_match:
                    recipe_data['prep_time'] = int(prep_match.group(1))
            
            if "COOK_TIME:" in gemini_response:
                cook_match = re.search(r'COOK_TIME:\s*(\d+)', gemini_response)
                if cook_match:
                    recipe_data['cook_time'] = int(cook_match.group(1))
            
            if "TOTAL_TIME:" in gemini_response:
                total_match = re.search(r'TOTAL_TIME:\s*(\d+)', gemini_response)
                if total_match:
                    recipe_data['total_time'] = int(total_match.group(1))
            
            # Calculate total time if not provided
            if not recipe_data['total_time'] and recipe_data['prep_time'] and recipe_data['cook_time']:
                recipe_data['total_time'] = recipe_data['prep_time'] + recipe_data['cook_time']
            
            # Extract ingredients
            if "INGREDIENTS:" in gemini_response:
                ingredients_section = gemini_response.split("INGREDIENTS:")[1]
                if "INSTRUCTIONS:" in ingredients_section:
                    ingredients_section = ingredients_section.split("INSTRUCTIONS:")[0]
                
                ingredients = []
                for line in ingredients_section.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•')):
                        ingredient = line.lstrip('-•').strip()
                        if ingredient:
                            ingredients.append(ingredient)
                recipe_data['ingredients'] = ingredients
            
            # Extract instructions
            if "INSTRUCTIONS:" in gemini_response:
                instructions_section = gemini_response.split("INSTRUCTIONS:")[1]
                if "NUTRITION_INFO:" in instructions_section:
                    instructions_section = instructions_section.split("NUTRITION_INFO:")[0]
                elif "TAGS:" in instructions_section:
                    instructions_section = instructions_section.split("TAGS:")[0]
                elif "NOTES:" in instructions_section:
                    instructions_section = instructions_section.split("NOTES:")[0]
                
                instructions = []
                for line in instructions_section.split('\n'):
                    line = line.strip()
                    if line and re.match(r'^\d+\.', line):
                        instruction = re.sub(r'^\d+\.\s*', '', line)
                        if instruction:
                            instructions.append(instruction)
                recipe_data['instructions'] = instructions
            
            # Extract nutrition information
            if "NUTRITION_INFO:" in gemini_response:
                nutrition_section = gemini_response.split("NUTRITION_INFO:")[1]
                if "TAGS:" in nutrition_section:
                    nutrition_section = nutrition_section.split("TAGS:")[0]
                elif "NOTES:" in nutrition_section:
                    nutrition_section = nutrition_section.split("NOTES:")[0]
                
                # Extract calories
                calories_match = re.search(r'Calories:\s*(\d+)', nutrition_section, re.IGNORECASE)
                if calories_match:
                    recipe_data['calories'] = int(calories_match.group(1))
                
                # Extract macronutrients
                protein_match = re.search(r'Protein:\s*(\d+(?:\.\d+)?)', nutrition_section, re.IGNORECASE)
                if protein_match:
                    recipe_data['protein'] = float(protein_match.group(1))
                
                carbs_match = re.search(r'Carbs:\s*(\d+(?:\.\d+)?)', nutrition_section, re.IGNORECASE)
                if carbs_match:
                    recipe_data['carbs'] = float(carbs_match.group(1))
                
                fat_match = re.search(r'Fat:\s*(\d+(?:\.\d+)?)', nutrition_section, re.IGNORECASE)
                if fat_match:
                    recipe_data['fat'] = float(fat_match.group(1))
                
                fiber_match = re.search(r'Fiber:\s*(\d+(?:\.\d+)?)', nutrition_section, re.IGNORECASE)
                if fiber_match:
                    recipe_data['fiber'] = float(fiber_match.group(1))
            
            # Extract tags
            if "TAGS:" in gemini_response:
                tags_section = gemini_response.split("TAGS:")[1]
                if "NOTES:" in tags_section:
                    tags_section = tags_section.split("NOTES:")[0]
                
                tags_line = tags_section.split('\n')[0].strip()
                tags = [tag.strip() for tag in tags_line.split(',') if tag.strip()]
                recipe_data['tags'] = tags
            
            # Extract notes
            if "NOTES:" in gemini_response:
                notes_section = gemini_response.split("NOTES:")[1].strip()
                recipe_data['notes'] = notes_section
            
        except Exception as e:
            print(f"Error extracting recipe data: {e}")
        
        return recipe_data


class RecipeListView(APIView):
    """
    Enhanced API endpoint for listing recipes with search and filtering.
    """
    pagination_class = RecipePagination
    
    def get(self, request):
        try:
            search_serializer = RecipeSearchSerializer(data=request.query_params)
            if not search_serializer.is_valid():
                return Response(search_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            queryset = Recipe.objects.filter(is_active=True)
            
            # Apply filters
            query = search_serializer.validated_data.get('query')
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(ingredients__icontains=query)
                )
            
            meal_type = search_serializer.validated_data.get('meal_type')
            if meal_type:
                queryset = queryset.filter(meal_type=meal_type)
            
            cuisine_type = search_serializer.validated_data.get('cuisine_type')
            if cuisine_type:
                queryset = queryset.filter(cuisine_type__icontains=cuisine_type)
            
            difficulty = search_serializer.validated_data.get('difficulty')
            if difficulty:
                queryset = queryset.filter(difficulty=difficulty)
            
            cooking_time = search_serializer.validated_data.get('cooking_time')
            if cooking_time:
                queryset = queryset.filter(cooking_time=cooking_time)
            
            min_rating = search_serializer.validated_data.get('min_rating')
            if min_rating:
                queryset = queryset.filter(rating__gte=min_rating)
            
            max_servings = search_serializer.validated_data.get('max_servings')
            if max_servings:
                queryset = queryset.filter(servings__lte=max_servings)
            
            dietary_restrictions = search_serializer.validated_data.get('dietary_restrictions')
            if dietary_restrictions:
                for restriction in dietary_restrictions:
                    queryset = queryset.filter(dietary_restrictions__icontains=restriction)
            
            # Apply ordering
            ordering = search_serializer.validated_data.get('ordering', '-created_at')
            queryset = queryset.order_by(ordering)
            
            # Paginate results
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)
            
            if page is not None:
                serializer = RecipeListSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = RecipeListSerializer(queryset, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            print(f"RecipeListView error: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to retrieve recipes: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecipeDetailView(generics.RetrieveAPIView):
    """
    Enhanced API endpoint for retrieving a single recipe by its ID.
    """
    queryset = Recipe.objects.filter(is_active=True)
    serializer_class = RecipeSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')

class RecipeRatingView(APIView):
    """
    API endpoint for rating recipes with detailed debugging.
    """
    
    def post(self, request, recipe_id):
        try:
            print(f"📝 Rating submission for recipe {recipe_id}")
            print(f"Request data: {request.data}")
            
            # Check if recipe exists
            try:
                recipe = Recipe.objects.get(id=recipe_id, is_active=True)
                print(f"✅ Recipe found: {recipe.title}")
            except Recipe.DoesNotExist:
                print(f"❌ Recipe {recipe_id} not found")
                return Response(
                    {'error': 'Recipe not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create serializer and pass recipe context
            serializer = RecipeRatingSerializer(data=request.data)
            
            if not serializer.is_valid():
                print(f"❌ Serializer validation failed")
                print(f"Validation errors: {serializer.errors}")
                return Response(
                    {
                        'error': 'Invalid rating data',
                        'details': serializer.errors,
                        'received_data': request.data
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"✅ Serializer validation passed")
            print(f"Validated data: {serializer.validated_data}")
            
            # Get user IP for duplicate prevention
            user_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            if not user_ip:
                user_ip = '127.0.0.1'  # Default for local testing
            
            print(f"User IP: {user_ip}")
            
            # Check if user already rated this recipe
            existing_rating = RecipeRating.objects.filter(
                recipe=recipe,
                user_ip=user_ip
            ).first()
            
            if existing_rating:
                print(f"❌ User already rated this recipe (Rating ID: {existing_rating.id})")
                return Response(
                    {'error': 'You have already rated this recipe'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the rating with recipe
            rating = serializer.save(recipe=recipe, user_ip=user_ip)
            
            print(f"✅ Rating created with ID: {rating.id}")
            
            # Update recipe average rating
            recipe.update_rating(rating.rating)
            
            response_data = {
                'message': 'Rating submitted successfully',
                'rating': RecipeRatingSerializer(rating).data,
                'new_average': float(recipe.rating) if recipe.rating else 0,
                'total_ratings': recipe.rating_count
            }
            
            print(f"✅ Response data: {response_data}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Exception in rating submission: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class PopularRecipesView(APIView):
    """
    API endpoint for getting popular recipes.
    """
    
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
            
            # Get recipes ordered by view count and rating
            recipes = Recipe.objects.filter(
                is_active=True,
                view_count__gt=0
            ).order_by('-view_count', '-rating')[:limit]
            
            serializer = RecipeListSerializer(recipes, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeaturedRecipesView(APIView):
    """
    API endpoint for getting featured recipes.
    """
    
    def get(self, request):
        try:
            recipes = Recipe.objects.filter(
                is_active=True,
                is_featured=True
            ).order_by('-created_at')[:8]
            
            serializer = RecipeListSerializer(recipes, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecipeStatsView(APIView):
    """
    API endpoint for getting recipe statistics.
    """
    
    def get(self, request):
        try:
            total_recipes = Recipe.objects.filter(is_active=True).count()
            total_views = Recipe.objects.filter(is_active=True).aggregate(
                total=Sum('view_count')
            )['total'] or 0
            
            avg_rating = Recipe.objects.filter(
                is_active=True,
                rating__isnull=False
            ).aggregate(avg=Avg('rating'))['avg']
            
            popular_cuisines = Recipe.objects.filter(
                is_active=True,
                cuisine_type__isnull=False
            ).values('cuisine_type').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            stats = {
                'total_recipes': total_recipes,
                'total_views': total_views,
                'average_rating': round(avg_rating, 2) if avg_rating else 0,
                'popular_cuisines': list(popular_cuisines),
            }
            
            return Response(stats)
        except Exception as e:
            print(f"Stats error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def recipe_suggestions(request):
    """
    API endpoint for getting recipe suggestions based on ingredients.
    """
    try:
        ingredients = request.query_params.get('ingredients', '').split(',')
        ingredients = [ing.strip() for ing in ingredients if ing.strip()]
        
        if not ingredients:
            return Response(
                {'error': 'Please provide ingredients'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find recipes that contain any of the ingredients
        queryset = Recipe.objects.filter(is_active=True)
        for ingredient in ingredients:
            queryset = queryset.filter(ingredients__icontains=ingredient)
        
        recipes = queryset.order_by('-rating', '-view_count')[:5]
        serializer = RecipeListSerializer(recipes, many=True)
        
        return Response({
            'suggestions': serializer.data,
            'search_ingredients': ingredients
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def recipe_reviews(request, recipe_id):
    """
    API endpoint for getting recipe reviews.
    """
    try:
        recipe = Recipe.objects.get(id=recipe_id, is_active=True)
        reviews = RecipeRating.objects.filter(recipe=recipe).order_by('-created_at')
        serializer = RecipeRatingSerializer(reviews, many=True)
        return Response(serializer.data)
    except Recipe.DoesNotExist:
        return Response(
            {'error': 'Recipe not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )