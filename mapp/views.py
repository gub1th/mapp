from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.db import transaction
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseNotAllowed

from mapp.forms import LoginForm, RegisterForm, UserProfileForm, PostForm, PlaylistForm
from mapp.models import Profile, Post, Playlist, Comment, Rating

from dotenv import load_dotenv
import os
import json

# open ai imports
from openai import OpenAI
import openai

from PIL import Image


load_dotenv()

def login_action(request):
    context = {}

    # if get method, return the empty login page
    if request.method == 'GET':
        context['form'] = LoginForm()
        return render(request, 'login.html', context)

    # Validates the form.
    form = LoginForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, 'login.html', context)

    # Authenticate usr and login
    new_user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
    login(request, new_user)

    if 'remember-me' in request.POST and request.POST['remember-me'] == 'on':
        request.session.set_expiry(100000)
    return redirect(reverse('home_page'))


@transaction.atomic
def register_action(request):
    context = {}

    # if get method, return the empty register page
    if request.method == 'GET':
        context['form'] = RegisterForm()
        return render(request, 'register.html', context)

    # Validates the form.
    form = RegisterForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, 'register.html', context)

    # At this point, the form data is valid.  Register and login the user.
    new_user = User.objects.create_user(username=form.cleaned_data['username'],
                                        password=form.cleaned_data['password'],
                                        email=form.cleaned_data['email'],
                                        first_name=form.cleaned_data['first_name'],
                                        last_name=form.cleaned_data['last_name'])
    new_user.save()

    new_user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
    login(request, new_user)
    new_profile = Profile(user=new_user)
    new_profile.save()
    return redirect(reverse('home_page'))


@login_required
def logout_action(request):
    logout(request)
    return redirect(reverse('login'))

@login_required
def get_map_page(request):
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    print('the api key is', api_key)
    context = {
        'google_maps_api_key': api_key,
    }
    return render(request, 'map_page.html', context)


@login_required
def map_page_action(request):
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    print('the api key is', api_key)
    context = {
        'google_maps_api_key': api_key,
        'form': PostForm(),
        'detail_post': -1
    }

    if request.method == 'GET':
        return render(request, 'map_page.html', context)


    new_post = Post(text=request.POST['text'],
                    latitude=float(request.POST['latitude']),
                    longitude=float(request.POST['longitude']),
                    title=request.POST['title'],
                    terrain=request.POST['terrain'],
                    user=request.user
                   )

    form = PostForm(request.POST, request.FILES)
    if not form.is_valid():
        context = {'google_maps_api_key': api_key, 'form': PostForm(), 'detail_post': -1}
        return render(request, 'map_page.html', context)

    image = form.cleaned_data['image']
    new_post.image = form.cleaned_data['image']
    new_post.content_type = form.cleaned_data['image'].content_type
    new_post.save()

    posts = Post.objects.all()
    context = {'google_maps_api_key': api_key,
               'form': PostForm(),
               'posts': posts,
               'detail_post': -1
              }

    return render(request, 'map_page.html', context)


@transaction.atomic
def new_rating_action(request):
    if not request.user.is_authenticated:
        return _my_json_error_response("You must be logged in to do this operation", status=401)
    if request.method != 'POST':
        return _my_json_error_response("You must use a POST request for this operation", status=405)
    if 'rating' not in request.POST or not request.POST['rating'].isdigit():
        return _my_json_error_response("You need to rate", status=405)
    if int(request.POST['rating']) > 5 or int(request.POST['rating']) < 1:
        return _my_json_error_response("bad rate", status=405)

    posts = Post.objects.filter(id=int(request.POST['for_post']))
    if len(posts) <= 0:
        return _my_json_error_response("Post not found", status=404)
    for_post = posts[0]

    ratings = Rating.objects.filter(user=request.user).filter(post=for_post)
    if len(ratings) > 0:
        rating = ratings[0]
        rating.rating = request.POST['rating']
        rating.save()
        all_rating = Rating.objects.filter(post=for_post)
        rating_sum = 0
        for i in range(len(all_rating)):
            print(all_rating[i].rating)
            rating_sum = rating_sum + all_rating[i].rating
        for_post.rating = round(rating_sum / len(all_rating),2)
        for_post.save()
        return HttpResponse(json.dumps({'status':'success'}), content_type='application/json')

    newRating = Rating(user = request.user, post=for_post, rating=request.POST['rating'])
    newRating.save()
    all_rating = Rating.objects.filter(post=for_post)
    rating_sum = 0
    for i in range(len(all_rating)):
        rating_sum = rating_sum + all_rating[i].rating
    for_post.rating = round(rating_sum / len(all_rating),2)
    for_post.save()
    return HttpResponse(json.dumps({'status':'success'}), content_type='application/json')

def add_comment_action(request):
    if not request.user.is_authenticated:
        return _my_json_error_response("You must be logged in to do this operation", status=401)
    if request.method != 'POST':
        return _my_json_error_response("You must use a POST request for this operation", status=405)
    if ('text' not in request.POST or not request.POST['text'] or 'for_post' not in request.POST or not request.POST['for_post']):
        return _my_json_error_response("You must enter text.", status=400)
    if (not request.POST['for_post'].isdigit()):
        return _my_json_error_response("You must enter a valid post ID.", status=400)

    posts = Post.objects.filter(id=int(request.POST['for_post']))
    if len(posts) > 0:
        for_post = posts[0]
        newComment = Comment(
                text=request.POST['text'],
                user=request.user,
                post=for_post,
                likes=0
            )

        newComment.save()
    return HttpResponse(json.dumps({'statue':'success'}), content_type='application/json')




def add_post_action(request):
    if not request.user.is_authenticated:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    if request.method != 'POST':
        return _my_json_error_response("You must use a POST request for this operation", status=405)


    if ('title' not in request.POST or not request.POST['title']):
        return _my_json_error_response("You must enter a title.", status=400)
    if ('text' not in request.POST or not request.POST['text']):
        return _my_json_error_response("You must enter text.", status=400)
    if ('terrain' not in request.POST or not request.POST['terrain']):
        return _my_json_error_response("You must enter a terrain.", status=400)
    if ('diff' not in request.POST or not request.POST['diff']):
        return _my_json_error_response("You must enter a difficulty.", status=400)
    if ('longitude' not in request.POST or not request.POST['longitude']):
        return _my_json_error_response("You must enter a longitude.", status=400)
    if ('latitude' not in request.POST or not request.POST['latitude']):
        return _my_json_error_response("You must enter a latitude.", status=400)
    if ('image' not in request.FILES or not request.FILES['image']):
        return _my_json_error_response("You must enter an image.", status=400)
    if (not (-180 <= float(request.POST['longitude']) <= 180)):
       return _my_json_error_response("You must enter a valid longitude.", status=400)
    if (not (-85 <= float(request.POST['latitude']) <= 85)):
       return _my_json_error_response("You must enter a valid latitude.", status=400)
    if (not (1 <= int(request.POST['diff']) <= 5)):
       return _my_json_error_response("You must enter a valid difficulty.", status=400)
    if ('x' not in request.POST or not request.POST['x']):
        return _my_json_error_response("Cropper X value missing.", status=400)
    if ('y' not in request.POST or not request.POST['y']):
        return _my_json_error_response("Cropper Y value missing.", status=400)
    if ('width' not in request.POST or not request.POST['width']):
        return _my_json_error_response("Cropper width missing.", status=400)
    if ('height' not in request.POST or not request.POST['height']):
        return _my_json_error_response("Cropper height missing.", status=400)
    if (not request.POST['x'].lstrip("-").isdigit()):
        return _my_json_error_response("Invalid X value for Cropper.", status=400)
    if (not request.POST['y'].lstrip("-").isdigit()):
        return _my_json_error_response("Invalid Y value for Cropper.", status=400)
    if (not request.POST['width'].lstrip("-").isdigit()):
        return _my_json_error_response("Invalid width value for Cropper.", status=400)
    if (not request.POST['height'].lstrip("-").isdigit()):
        return _my_json_error_response("Invalid height value for Cropper.", status=400)



    newPost = Post(
               title=request.POST['title'],
               text=request.POST['text'],
               terrain=request.POST['terrain'],
               diff=request.POST['diff'],
               longitude=request.POST['longitude'],
               latitude=request.POST['latitude'],
               image=request.FILES.get("image"),
               user=request.user
              )

    newPost.save()
    x = int(request.POST['x'])
    y = int(request.POST['y'])
    width = int(request.POST['width'])
    height = int(request.POST['height'])

    image = Image.open(newPost.image)
    croppedImage = image.crop((x, y, x+width, y+height))
    croppedImage.save(newPost.image.path)
    newPostJSON = {
            'id': newPost.id,
            'title': newPost.title,
            'text': newPost.text,
            'terrain': newPost.terrain,
            'latitude': newPost.latitude,
            'longitude': newPost.longitude,
            'rating': newPost.rating,
            'difficulty': newPost.diff,
            'userID': newPost.user.id,
        }

    response_data = {'posts': newPostJSON}

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type='application/json')

# generate feed using GPT based on preferences for user
@login_required
def get_feed_page(request):

    # obtain key from local .env
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI()

    # obtain all posts from model
    all_posts_data = Post.objects.all()
    all_posts_list = list(all_posts_data)

    # get user data
    user_profile = Profile.objects.filter(user=request.user)

    #attribute 1
    if len(user_profile) == 0:
        atr1 = "what the average person likes"
    else:
        atr1 = user_profile[0].bio

    locations = ""
    for post in all_posts_list:
        locations += "id=" + str(post.id) + " " + post.title + ", "

    # remove leading comma at end of str locations


    if len(locations) > 2 and locations[-2:] == ", ":
        locations = locations[:-2]



    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You rank provided posts in terms of relevance to " + atr1},
            {"role": "system", "content": "LOCATIONS: " + locations},
            {"role": "system", "content": "output must be in this format: id|name\nid|name\n etc..."},
            {"role": "system", "content": "also, output all of the provided locations in the provided format"},
            {"role": "user", "content": "Return the rankings with associated inputs: id|name\nid|name\n etc..."}
        ],
        temperature=0.1
    )
    # parsing logic for taking gpt output and turning it into suggestion format
    posts_str = completion.choices[0].message.content
    lines = posts_str.split("\n")
    lines = lines
    posts = []
    rank = 0
    if len(locations) == 0:
        context = {'posts': posts}
        return render(request, 'other_playlist.html', context)

    for line in lines:
        acc_post = ""

        terms = line.split("|")


        if terms[0].isdigit():
            post_id = int(terms[0])
        else:
            context = {'posts': posts}
            return render(request, 'other_playlist.html', context)

        post_data = Post.objects.filter(id=post_id)

        if len(post_data) > 0:
            acc_post = post_data[0]
            post_id = acc_post.id
            post_name = acc_post.title
        else:
            context = {'posts': posts}
            return render(request, 'other_playlist.html', context)

        # post_name = acc_post.title
        rank += 1
        post = {'id': post_id, 'name': post_name, 'rank': rank}
        posts.append(post)

    context = {'posts': posts}


    return render(request, 'other_playlist.html', context)


# takes search bar input and outputs ranking
@login_required
def get_search_feed(request):

    if request.method != 'GET':
        return _my_json_error_response("You must use a GET request for this operation", status=405)

    # obtain key from local .env
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI()

    # obtain all posts from model
    all_posts_data = Post.objects.all()
    all_posts_list = list(all_posts_data)

    # attribute 1 - search input
    atr1 = request.GET.get('q', '')

    # locations data
    locations = ""
    for post in all_posts_list:
        locations += "id=" + str(post.id) + " " + post.title + ", "

    # remove leading comma at end of str locations
    if len(locations) > 2 and locations[-2:] == ", ":
        locations = locations[:-2]

    # gpt logic
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You rank provided locations in terms of relevance to " + atr1},
            {"role": "system", "content": "LOCATIONS: " + locations},
            {"role": "system", "content": "output must be in this format: id|name\nid|name\n etc..."},
            {"role": "user", "content": "Return the rankings with associated inputs: id|name\nid|name\n etc..."}
        ],
        temperature=0.4
    )

    # parsing logic for taking gpt output and turning it into suggestion format
    posts_str = completion.choices[0].message.content
    lines = posts_str.split("\n")
    posts = []

    # id, name (rank in order)
    rank = 0
    if len(locations) == 0:
        return JsonResponse(posts, safe=False)

    # parse
    if len(lines) < 5:
        sugg_len = len(lines)
    else:
        sugg_len = 5
    for i in range(sugg_len):
        terms = lines[i].split("|")


        if terms[0].isdigit():
            post_id = int(terms[0])
        else:
            context = {'posts': posts}
            return render(request, 'other_playlist.html', context)

        post_data = Post.objects.filter(id=post_id)
        
        if len(post_data) > 0:
            acc_post = post_data[0]
            post_id = acc_post.id
            post_name = acc_post.title
        else:
            context = {'posts': posts}
            return render(request, 'other_playlist.html', context)

        rank += 1
        post = {'id': post_id, 'name': post_name, 'rank': rank}
        posts.append(post)

    return JsonResponse(posts, safe=False)


@login_required
@transaction.atomic
def profile_action(request):

    #Check if profile exist
    retProfiles = Profile.objects.filter(user=request.user)
    if len(retProfiles) == 0 :
        newProfileUser = User.objects.filter(id=request.user.id)
        if (len(newProfileUser) != 0):
            new_profile = Profile(user=request.user)
            new_profile.save()
    user_profile = get_object_or_404(Profile, user=request.user)

    #get stats data
    user_playlists = Playlist.objects.filter(user=request.user)
    locations_added_count = Post.objects.filter(user=request.user).count()
    comments_made_count = Comment.objects.filter(user=request.user).count()

    avg_post_rating = Post.objects.filter(user=request.user).aggregate(Avg('rating'))['rating__avg']
    if avg_post_rating is None:
        avg_post_rating = 0

    # initialize forms
    user_profile_form = UserProfileForm(instance=user_profile)
    playlist_form = PlaylistForm()

    if request.method == 'POST':
        if 'bio' in request.POST or 'profile_picture' in request.POST:
            print("here")
            user_profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            print(user_profile_form)
            if user_profile_form.is_valid():
                user_profile_form.save()
                return redirect('profile')
            else:
                print("User profile form is not valid")
                bio = user_profile_form.cleaned_data.get('bio')
                if bio is not None:
                    user_profile.bio = bio
                    user_profile.save()
                    print("but bio is valid")

        if 'playlist' in request.POST:
            playlist_form = PlaylistForm(request.POST)
            if playlist_form.is_valid():
                new_playlist = playlist_form.save(commit=False)
                new_playlist.user = request.user
                new_playlist.save()
                return redirect('profile')
            else:
                print("Playlist form is not valid")

        context = {
            'user_profile_form': user_profile_form,
            'playlist_form': playlist_form,
            'user_playlists': user_playlists,
            'locations_added_count': locations_added_count,
            'avg_post_rating': round(avg_post_rating, 1),
            'comments_made_count': comments_made_count,
        }
        request.user.profile = user_profile
        return render(request, 'profile.html', context)

    context = {
        'user_profile_form': user_profile_form,
        'playlist_form': playlist_form,
        'user_playlists': user_playlists,
        'locations_added_count': locations_added_count,
        'avg_post_rating': round(avg_post_rating, 1),
        'comments_made_count': comments_made_count,
    }
    request.user.profile = user_profile
    return render(request, 'profile.html', context)


@login_required
@transaction.atomic
def other_profile_action(request, id):
    retProfileUsers = User.objects.filter(id=id)
    if len(retProfileUsers) == 0:
        return render(request, 'map_page.html', context)

    retProfileUser = retProfileUsers[0]
    retProfiles = Profile.objects.filter(user=retProfileUser)
    if len(retProfiles) == 0 :
        newProfileUser = User.objects.filter(id=request.user.id)
        if (len(newProfileUser) != 0):
            new_profile = Profile(user=retProfileUser)
            new_profile.save()


    profile = get_object_or_404(Profile, user=retProfileUser)

    user_profile = get_object_or_404(Profile, user=request.user)
    request.user.profile = user_profile

    if profile.id == request.user.profile.id:
        user_profile_form = UserProfileForm(request.POST or None, request.FILES or None, instance=profile)
        playlist_form = PlaylistForm()

        user_playlists = Playlist.objects.filter(user=request.user)
        locations_added_count = Post.objects.filter(user=request.user).count()
        comments_made_count = Comment.objects.filter(user=request.user).count()

        avg_post_rating = Post.objects.filter(user=request.user).aggregate(Avg('rating'))['rating__avg']
        if avg_post_rating is None:
            avg_post_rating = 0

        context = {
            'user_profile_form': user_profile_form,
            'playlist_form': playlist_form,
            'user_playlists': user_playlists,
            'locations_added_count': locations_added_count,
            'avg_post_rating': round(avg_post_rating, 1),
            'comments_made_count': comments_made_count,
        }

        return render(request, 'profile.html', context)

    user_playlists = Playlist.objects.filter(user=profile.user)
    locations_added_count = Post.objects.filter(user=profile.user).count()
    comments_made_count = Comment.objects.filter(user=profile.user).count()
    avg_post_rating = Post.objects.filter(user=profile.user).aggregate(Avg('rating'))['rating__avg']
    if avg_post_rating is None:
        avg_post_rating = 0

    context = {
        'profile': profile,
        'locations_added_count': locations_added_count,
        'comments_made_count': comments_made_count,
        'avg_post_rating': round(avg_post_rating, 1),
        'user_playlists': user_playlists
    }
    return render(request, 'other_profile.html', context)


@login_required
def follow(request, id):
    user_to_follow = get_object_or_404(User, id=id)
    request.user.profile.following.add(user_to_follow)
    request.user.profile.save()

    user_playlists = Playlist.objects.filter(user=user_to_follow.profile.user)
    locations_added_count = Post.objects.filter(user=user_to_follow.profile.user).count()
    comments_made_count = Comment.objects.filter(user=user_to_follow.profile.user).count()
    avg_post_rating = Post.objects.filter(user=user_to_follow.profile.user).aggregate(Avg('rating'))['rating__avg']
    if avg_post_rating is None:
        avg_post_rating = 0

    context = {
        'profile': user_to_follow.profile,
        'locations_added_count': locations_added_count,
        'comments_made_count': comments_made_count,
        'avg_post_rating': round(avg_post_rating, 1),
        'user_playlists': user_playlists
    }
    return render(request, 'other_profile.html', context)


@login_required
def unfollow(request, id):
    user_to_unfollow = get_object_or_404(User, id=id)
    request.user.profile.following.remove(user_to_unfollow)
    request.user.profile.save()

    user_playlists = Playlist.objects.filter(user=user_to_unfollow.profile.user)
    locations_added_count = Post.objects.filter(user=user_to_unfollow.profile.user).count()
    comments_made_count = Comment.objects.filter(user=user_to_unfollow.profile.user).count()
    avg_post_rating = Post.objects.filter(user=user_to_unfollow.profile.user).aggregate(Avg('rating'))['rating__avg']
    if avg_post_rating is None:
        avg_post_rating = 0

    context = {
        'profile': user_to_unfollow.profile,
        'locations_added_count': locations_added_count,
        'comments_made_count': comments_made_count,
        'avg_post_rating': round(avg_post_rating, 1),
        'user_playlists': user_playlists
    }
    return render(request, 'other_profile.html', context)


def get_global(request):
    if not request.user.is_authenticated:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    response_data = {key:[] for key in ["posts"]}

    for model_item in Post.objects.all():
        my_item = {
            'id': model_item.id,
            'text': model_item.text,
            'user': model_item.user.username,
            'terrain': model_item.terrain,
            'title': model_item.title,
            'rating': model_item.rating,
            'difficulty': model_item.diff,
            'latitude': model_item.latitude,
            'longitude': model_item.longitude,
        }
        response_data["posts"].append(my_item)

    response_data["playlists"] = []
    for playlist in Playlist.objects.filter(user=request.user):
        my_playlist = {
            'id': playlist.id,
            'name': playlist.name,
            'user': request.user.username,
            'postIds': [post.id for post in playlist.posts.all()]
        }
        response_data["playlists"].append(my_playlist)

    response_json = json.dumps(response_data)

    return HttpResponse(response_json, content_type='application/json')


def get_photo(request, id):
    item = get_object_or_404(Post, id=id)

    # Maybe we don't need this check as form validation requires a picture be uploaded.
    # But someone could have delete the picture leaving the DB with a bad references.
    if not item.image:
        raise Http404

    return HttpResponse(item.image, content_type=item.content_type)


def get_post(request, id):
    post = get_object_or_404(Post, id=id)
    print()
    comments = []
    for comment in Comment.objects.filter(post=post):
        comments.append({'name':comment.user.first_name + ' ' + comment.user.last_name , 'text':comment.text, 'userId': comment.user.id})
    print(comments)
    postJSON = {
            'id': post.id,
            'title': post.title,
            'text': post.text,
            'terrain': post.terrain,
            'latitude': post.latitude,
            'longitude': post.longitude,
            'rating': post.rating,
            'difficulty': post.diff,
            'userID': post.user.id,
            'userName': post.user.first_name,
        }

    playlistList = []
    for playlist in Playlist.objects.filter(user=request.user):
        my_playlist = {
            'id': playlist.id,
            'name': playlist.name,
            'user': request.user.username,
            'postIds': [post.id for post in playlist.posts.all()]
        }
        playlistList.append(my_playlist)

    response_data = {'post': postJSON, 'comments':comments, 'playlists':playlistList}
    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type='application/json')


def get_photo_profile(request, id):
    item = get_object_or_404(Profile, id=id)

    # Maybe we don't need this check as form validation requires a picture be uploaded.
    # But someone could have delete the picture leaving the DB with a bad references.
    if not item.profile_picture:
        raise Http404

    return HttpResponse(item.profile_picture, content_type=item.content_type)


def _my_json_error_response(message, status=200):
    response_json = '{"error": "' + message + '"}'
    return HttpResponse(response_json, content_type='application/json', status=status)


@login_required
def get_playlist(request, id):
    playlist = get_object_or_404(Playlist, id=id)
    posts = playlist.posts.all()
    if request.user != playlist.user :
        return render(request, 'others_playlist.html', {"playlist":playlist, "posts":posts})

    return render(request, 'playlist.html', {"playlist":playlist, "posts":posts})


@login_required
def delete_playlist(request, id):
    playlist_to_delete = get_object_or_404(Playlist, id=id)
    if (request.user == playlist_to_delete.user):
        playlist_to_delete.delete()
    return redirect('profile')


@login_required
def delete_post_from_playlist(request, id):
    playlist = get_object_or_404(Playlist, id=id)
    post_id = request.POST.get('post_id')
    if post_id:
        if request.user != playlist.user:
            return redirect('playlist_detail', id=playlist.id)

        post = get_object_or_404(Post, id=post_id)
        playlist.posts.remove(post)
        playlist.save()
        return redirect('playlist_detail', id=playlist.id)
    else:
        return _my_json_error_response('Invalid post ID')


# adding post to playlists based on checkbox
@login_required
def update_playlists(request):
    if request.method == 'POST':
        print(request.POST)
        post_id = request.POST.get('postId')
        playlist_ids = request.POST.getlist('playlistIds[]')
        print("UP1")
        print(post_id)
        print(playlist_ids)
        if post_id:
            print("UP2")
            post = get_object_or_404(Post, id=post_id)
            for playlist_id in playlist_ids:
                playlist = get_object_or_404(Playlist, id=playlist_id)
                print(playlist)
                # dont want duplicates, so check if the post is already in the playlist
                if post in playlist.posts.all():
                    print("contin")
                    continue
                print("not continu")
                playlist.posts.add(post)
                playlist.save()

            return HttpResponse(json.dumps({'TODO':'do something'}), content_type='application/json')
        else:
            print("UP3")
            return _my_json_error_response('Invalid post ID')


@login_required
def playlist_post_detail(request, id):
    return redirect(reverse('map_page/'+str(id)))


@login_required
def map_page_action_detail(request,id):
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')

    detail_posts = Post.objects.filter(id=id)
    if len(detail_posts) == 0:
        id = -1

    context = {
        'google_maps_api_key': api_key,
        'form': PostForm(),
        'detail_post': id
    }

    if request.method == 'GET':
        return render(request, 'map_page.html', context)


    new_post = Post(text=request.POST['text'],
                    latitude=float(request.POST['latitude']),
                    longitude=float(request.POST['longitude']),
                    title=request.POST['title'],
                    terrain=request.POST['terrain'],
                    user=request.user
                   )

    form = PostForm(request.POST, request.FILES)
    if not form.is_valid():
        context = {'google_maps_api_key': api_key, 'form': PostForm(), 'detail_post': -1}
        return render(request, 'map_page.html', context)

    image = form.cleaned_data['image']
    new_post.image = form.cleaned_data['image']
    new_post.content_type = form.cleaned_data['image'].content_type
    new_post.save()

    posts = Post.objects.all()
    context = {'google_maps_api_key': api_key,
               'form': PostForm(),
               'posts': posts,
               'detail_post': -1
              }


    return render(request, 'map_page.html', context)


#Google login pipeline functhion
def save_profile(backend, user, response, *args, **kwargs):
    profiles = Profile.objects.filter(user=user)
    if len(profiles) <= 0:
        new_profile = Profile(user=user)
        new_profile.save()
