from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Post(models.Model):
    title = models.CharField(default="", max_length=25)
    text = models.CharField(default="", max_length=250)
    terrain = models.CharField(default="mountain-sun", max_length=200)
    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    image = models.FileField(blank=True)
    diff = models.FloatField(default=1.2)
    rating = models.FloatField(default=3.5)
    longitude = models.FloatField()
    latitude = models.FloatField()
    content_type = models.CharField(blank=True, max_length=50)

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    post = models.ForeignKey(Post, default=None, on_delete=models.PROTECT, related_name="rating_post")
    rating = models.IntegerField()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    bio = models.TextField(default='')
    profile_picture = models.FileField(blank=True, upload_to='profile_picture/')
    following = models.ManyToManyField(User, related_name="followers")
    content_type = models.CharField(max_length=50, default = '')
    favorite_locs = models.ManyToManyField(Post, related_name="favorite_locs")

class Comment(models.Model):
    text = models.CharField(max_length=200)
    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    post = models.ForeignKey(Post, default=None, on_delete=models.PROTECT)
    likes = models.IntegerField()

# class Rating(models.Model):
#     rating = models.IntegerField()
#     user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
#     post = models.ForeignKey(Post, default=None, on_delete=models.PROTECT)

class Playlist(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    posts = models.ManyToManyField(Post, related_name='playlists', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} by {self.user.username}"
