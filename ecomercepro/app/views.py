from django.shortcuts import render , reverse , redirect
#from google.generativeai.types.generation_types import StopCandidateException
from django.http import HttpResponse ,  HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
import uuid
from django.db.models import Count, Avg, F
from .models import *
import time
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.db.models import Q

def index(request):
    value = session_id(request)
    products = Product.objects.all().order_by('-like')[:4]
    prod = Product.objects.all()[:10]
    print("products :- ",products)
    #context = {'products':products}
    recommended = recommend_products(request)
    user_bag = bag.objects.filter(session_id=value)
    product_ids = [item.product.id for item in user_bag]
    products = Product.objects.filter(pk__in=product_ids)

    context = {'recommended':recommended,
                'products':products,
                'prod':prod,
                'products':products,
    }
    print("Recommendation in index :- ",context)
    return render(request, 'index.html',context)


def product(request,slug):
    value = session_id(request)
    prod = Product.objects.filter(p_id=slug).first()
    print("Prod:- ",prod.p_id)
    save_time_spent(request)
    if 'productId' in request.COOKIES:
        product_id = request.COOKIES['productId']
    recommended  = recommend_products(request)
    user_bag = bag.objects.filter(session_id=value)
    product_ids = [item.product.id for item in user_bag]
    products = Product.objects.filter(pk__in=product_ids)
    print("Recommended Resoponse:- ",recommended)
    first_two = prod.p_id // 100
    simi_pro = Product.objects.filter(Q(p_id__startswith=first_two) | Q(p_id=first_two))[:3]
    print("Similiar products:- ", simi_pro)
    context = {'prod':prod,
                'recommended':recommended,
                'simi_pro':simi_pro,
                'products':products,
        }
    return render(request,'product.html',context)

def addtobag(request):
    session_id(request)
    """product_id = None
    if 'productId' in request.COOKIES:
        product_id = request.COOKIES['productId']"""
    #print("Product ID : - ",product_id)
    value = request.session.get('key')
    if request.method == 'POST':
        print("Inside the size")
        size = request.POST.get('Size')
        product_id = request.POST.get('p_id')
        print("Size :- ",size)
        product = Product.objects.get(p_id=product_id)
        user_activity.objects.create(session_id=value,action="ADD_TO_BAG",product=product)
        bag.objects.create(session_id=value,size=size,product=product) 
        return HttpResponseRedirect(product_id)
    
    return JsonResponse({'error': 'Failed to add to bag'})

def save_time_spent(request):
    if request.method == 'POST':
        session_id = request.session.get('key')
        product_id = request.POST.get('product_id')
        time_spent = request.POST.get('time_spent')
        print("Time spent is : ",time_spent)
        try:
            product = Product.objects.get(p_id=product_id)
            UserActivity.objects.create(
                session_id=session_id,
                action="TIME_SPENT",
                product=product,
                timespent=time_spent
            )
            print("Succces")
            return JsonResponse({'success': True})  # Indicate success
        except Exception as e:
            return JsonResponse({'error': str(e)})  # Return error message
    else:
        return JsonResponse({'error': 'Invalid request'})
def save_like(request):
    value = request.session.get('key')
    if request.method == 'POST':
        product_id = request.POST.get('p_id')
        print("Product_id :- ",product_id)
        product = Product.objects.get(p_id=product_id)
        user_activity.objects.create(session_id=value,action="LIKE",product=product)
        return HttpResponseRedirect(product_id)
    return JsonResponse({'error': 'Failed to save like'})

def session_id(request):
    if 'key' not in request.session:
        id = generate_unique_chat_id()
        request.session['key']=id
        request.session.modified = True
        return id
    else:
        value = request.session.get('key')
        print(value)
        return value


def generate_unique_chat_id():
    timestamp = int(time.time() * 100)  # Convert current timestamp to milliseconds
    random_num = random.randint(10000, 99999)  # Generate a random 5-digit number
    random_sub = random.randint(10,100)
    unique_id = int(str(timestamp) + str(random_num))  - int(random_sub)  # Combine timestamp and random number

    return unique_id


def get_product_recommendations(user_activities, num_recommendations=2):
    """
    Generates product recommendations based on user activity and product descriptions,
    prioritizing products added to the bag.
    """
    
    user_sessions = user_activity.objects.filter(session_id=user_activities.session_id).order_by('-timestamp')
    print("user session activity :- ",user_sessions)
    # Combine user activity data and product descriptions for more comprehensive similarity
    combined_features = []
    for activity in user_sessions:
        features = [
            activity.action,  # User action (LIKE, VIEW, ADD_TO_BAG, TIME_SPENT)
            activity.product.name,  # Product name
            activity.product.description,  # Product description
        ]
        if activity.action == 'ADD_TO_BAG':  # Give extra weight to added-to-bag items
            features.append("added_to_bag")  # Add a keyword for boost
        combined_features.append(" ".join(str(f) for f in features))

    # Vectorize the combined features using TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(combined_features)

    # Calculate cosine similarity between products
    similarities = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Get the latest product the user interacted with
    recent_product_index = len(user_sessions) - 1
    similarity_scores = similarities[recent_product_index]

    # Sort by similarity and filter out the recent product
    top_product_indices = np.argsort(similarity_scores)[::-1]
    recommendations = []
    for i in top_product_indices:
        i = int(i)
        if i != recent_product_index:  # Avoid recommending the same product
            recommendations.append(user_sessions[i].product)
            if len(recommendations) >= num_recommendations:
                break
    print("REcommendation in the algo :- ",recommendations)
    return recommendations

def recommend_products(request):
    """
    View to display product recommendations.
    """
    if 'key' in request.session:
        user_session_id = request.session['key']
        print("User session id :- ",user_session_id)
        
        # Get the latest user activity 
        user_activities = user_activity.objects.filter(session_id=user_session_id).order_by('-timestamp').first()
        print("user activity data in recommend :- ",user_activities)
        if user_activities:
            recommendations = get_product_recommendations(user_activities)
            print("Recommendation algorithm :- ",recommendations)
            #context = {'recommendations': recommendations}
            return recommendations
        else:
            # If no recent activity, recommend based on popularity and number of bags
            recommendations = Product.objects.annotate(
                avg_rating=Avg('userrating__rating'),
                bag_count=Count('useractivity', filter=Q(useractivity__action='ADD_TO_BAG'))
            ).order_by('-bag_count', '-avg_rating')[:6]
            #context = {'recommendations': recommendations}
            return recommendations

       
    else:
        return HttpResponseRedirect(reverse('product'))
#recommend_products()