import json
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from .db_utils import load_db, save_db, get_next_id, find_by_id, find_user_by_username

def get_json_body(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

@ensure_csrf_cookie
def home_view(request):
    response = render(request, 'home.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@ensure_csrf_cookie
def community_view(request):
    response = render(request, 'community.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@ensure_csrf_cookie
def login_signup_view(request):
    response = render(request, 'login_signup.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@ensure_csrf_cookie
def place_details_view(request, venue_id=None):
    response = render(request, 'place_details.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@ensure_csrf_cookie
def profile_page_view(request, user_id=None):
    response = render(request, 'profile_page.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@require_http_methods(["POST"])
def api_register(request):
    body = get_json_body(request)
    if not body:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    username = body.get('username', '').strip()
    password = body.get('password', '')
    
    if not username or not password:
        return JsonResponse({'error': 'Username and password are required'}, status=400)
    
    if len(username) < 3:
        return JsonResponse({'error': 'Username must be at least 3 characters'}, status=400)
    
    if len(password) < 6:
        return JsonResponse({'error': 'Password must be at least 6 characters'}, status=400)
    
    existing_user = find_user_by_username(username)
    if existing_user:
        return JsonResponse({'error': 'Username already exists'}, status=400)
    
    data = load_db()
    new_user = {
        'id': get_next_id(data['users']),
        'username': username,
        'password_hash': make_password(password)
    }
    data['users'].append(new_user)
    save_db(data)
    
    request.session['user_id'] = new_user['id']
    request.session['username'] = new_user['username']
    
    return JsonResponse({
        'message': 'Registration successful',
        'user': {'id': new_user['id'], 'username': new_user['username']}
    })

@require_http_methods(["POST"])
def api_login(request):
    body = get_json_body(request)
    if not body:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    username = body.get('username', '').strip()
    password = body.get('password', '')
    
    if not username or not password:
        return JsonResponse({'error': 'Username and password are required'}, status=400)
    
    user = find_user_by_username(username)
    if not user:
        return JsonResponse({'error': 'Invalid username or password'}, status=401)
    
    if not check_password(password, user['password_hash']):
        return JsonResponse({'error': 'Invalid username or password'}, status=401)
    
    request.session['user_id'] = user['id']
    request.session['username'] = user['username']
    
    return JsonResponse({
        'message': 'Login successful',
        'user': {'id': user['id'], 'username': user['username']}
    })

@require_http_methods(["POST"])
def api_logout(request):
    request.session.flush()
    return JsonResponse({'message': 'Logged out successfully'})

@require_http_methods(["GET"])
def api_me(request):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    
    if user_id and username:
        return JsonResponse({
            'logged_in': True,
            'user': {'id': user_id, 'username': username}
        })
    return JsonResponse({'logged_in': False, 'user': None})

@require_http_methods(["GET"])
def api_venues_list(request):
    data = load_db()
    venues = []
    for venue in data['venues']:
        venue_reviews = [r for r in data['reviews'] if r['venue_id'] == venue['id']]
        avg_rating = 0
        if venue_reviews:
            avg_rating = round(sum(r['rating'] for r in venue_reviews) / len(venue_reviews), 1)
        venues.append({
            **venue,
            'avg_rating': avg_rating,
            'review_count': len(venue_reviews)
        })
    return JsonResponse({'venues': venues})

@require_http_methods(["GET"])
def api_venue_detail(request, venue_id):
    data = load_db()
    venue = find_by_id(data['venues'], venue_id)
    
    if not venue:
        return JsonResponse({'error': 'Venue not found'}, status=404)
    
    venue_reviews = [r for r in data['reviews'] if r['venue_id'] == venue_id]
    avg_rating = 0
    if venue_reviews:
        avg_rating = round(sum(r['rating'] for r in venue_reviews) / len(venue_reviews), 1)
    
    return JsonResponse({
        'venue': {
            **venue,
            'avg_rating': avg_rating,
            'review_count': len(venue_reviews)
        }
    })

@require_http_methods(["GET"])
def api_reviews_list(request):
    venue_id = request.GET.get('venue_id')
    data = load_db()
    
    reviews = data['reviews']
    if venue_id:
        try:
            venue_id = int(venue_id)
            reviews = [r for r in reviews if r['venue_id'] == venue_id]
        except ValueError:
            return JsonResponse({'error': 'Invalid venue_id'}, status=400)
    
    enriched_reviews = []
    for review in reviews:
        user = find_by_id(data['users'], review['user_id'])
        venue = find_by_id(data['venues'], review['venue_id'])
        enriched_reviews.append({
            **review,
            'username': user['username'] if user else 'Unknown User',
            'venue_name': venue['name'] if venue else 'Unknown Venue'
        })
    
    enriched_reviews.sort(key=lambda x: x['timestamp'], reverse=True)
    return JsonResponse({'reviews': enriched_reviews})

@require_http_methods(["POST"])
def api_reviews_create(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Login required'}, status=401)
    
    body = get_json_body(request)
    if not body:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    venue_id = body.get('venue_id')
    rating = body.get('rating')
    text = body.get('text', '').strip()
    
    if not venue_id or not rating:
        return JsonResponse({'error': 'venue_id and rating are required'}, status=400)
    
    try:
        venue_id = int(venue_id)
        rating = int(rating)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid venue_id or rating'}, status=400)
    
    if rating < 1 or rating > 5:
        return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
    
    data = load_db()
    venue = find_by_id(data['venues'], venue_id)
    if not venue:
        return JsonResponse({'error': 'Venue not found'}, status=404)
    
    new_review = {
        'id': get_next_id(data['reviews']),
        'user_id': user_id,
        'venue_id': venue_id,
        'rating': rating,
        'text': text,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    data['reviews'].append(new_review)
    save_db(data)
    
    user = find_by_id(data['users'], user_id)
    return JsonResponse({
        'message': 'Review created',
        'review': {
            **new_review,
            'username': user['username'] if user else 'Unknown',
            'venue_name': venue['name']
        }
    })

@require_http_methods(["PUT"])
def api_reviews_update(request, review_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Login required'}, status=401)
    
    data = load_db()
    review = find_by_id(data['reviews'], review_id)
    
    if not review:
        return JsonResponse({'error': 'Review not found'}, status=404)
    
    if review['user_id'] != user_id:
        return JsonResponse({'error': 'You can only edit your own reviews'}, status=403)
    
    body = get_json_body(request)
    if not body:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    if 'rating' in body:
        try:
            rating = int(body['rating'])
            if rating < 1 or rating > 5:
                return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
            review['rating'] = rating
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid rating'}, status=400)
    
    if 'text' in body:
        review['text'] = body['text'].strip()
    
    save_db(data)
    
    user = find_by_id(data['users'], user_id)
    venue = find_by_id(data['venues'], review['venue_id'])
    
    return JsonResponse({
        'message': 'Review updated',
        'review': {
            **review,
            'username': user['username'] if user else 'Unknown',
            'venue_name': venue['name'] if venue else 'Unknown'
        }
    })

@require_http_methods(["DELETE"])
def api_reviews_delete(request, review_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Login required'}, status=401)
    
    data = load_db()
    review = find_by_id(data['reviews'], review_id)
    
    if not review:
        return JsonResponse({'error': 'Review not found'}, status=404)
    
    if review['user_id'] != user_id:
        return JsonResponse({'error': 'You can only delete your own reviews'}, status=403)
    
    data['reviews'] = [r for r in data['reviews'] if r['id'] != review_id]
    save_db(data)
    
    return JsonResponse({'message': 'Review deleted'})

@require_http_methods(["GET"])
def api_user_profile(request, user_id):
    data = load_db()
    user = find_by_id(data['users'], user_id)
    
    if not user:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    user_reviews = [r for r in data['reviews'] if r['user_id'] == user_id]
    enriched_reviews = []
    for review in user_reviews:
        venue = find_by_id(data['venues'], review['venue_id'])
        enriched_reviews.append({
            **review,
            'venue_name': venue['name'] if venue else 'Unknown Venue'
        })
    
    enriched_reviews.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return JsonResponse({
        'user': {
            'id': user['id'],
            'username': user['username']
        },
        'reviews': enriched_reviews
    })

@require_http_methods(["GET"])
def api_feed(request):
    data = load_db()
    
    enriched_reviews = []
    for review in data['reviews']:
        user = find_by_id(data['users'], review['user_id'])
        venue = find_by_id(data['venues'], review['venue_id'])
        enriched_reviews.append({
            **review,
            'username': user['username'] if user else 'Unknown User',
            'venue_name': venue['name'] if venue else 'Unknown Venue'
        })
    
    enriched_reviews.sort(key=lambda x: x['timestamp'], reverse=True)
    return JsonResponse({'reviews': enriched_reviews})
