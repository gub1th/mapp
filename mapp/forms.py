from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from mapp.models import Profile, Post, Playlist

MAX_UPLOAD_SIZE = 25000000

class LoginForm(forms.Form):
    username = forms.CharField(max_length = 20)
    password = forms.CharField(max_length = 200, widget = forms.PasswordInput())

    def clean(self):
        cleaned_data = super().clean()
        # Confirms that the two password fields match
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError("Invalid username/password")
        return cleaned_data


class RegisterForm(forms.Form):
    username   = forms.CharField(max_length = 20)
    password  = forms.CharField(max_length = 200,label='Password',widget = forms.PasswordInput())
    confirm_password  = forms.CharField(max_length = 200,label='Confirm password',widget = forms.PasswordInput())
    email      = forms.CharField(max_length=50,widget = forms.EmailInput())
    first_name = forms.CharField(max_length=20)
    last_name  = forms.CharField(max_length=20)

    def clean(self):
        cleaned_data = super().clean()
        # Confirms that the two password fields match
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords did not match.")
        # We must return the cleaned data we got from our parent.
        return cleaned_data

    # Customizes form validation for the username field.
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.select_for_update().filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")
        return username

# class UserProfileForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ['bio', 'profile_picture']

#     def clean_profile_picture(self):
#         picture = self.cleaned_data['profile_picture']
#         if not picture or not hasattr(picture, 'content_type'):
#             raise forms.ValidationError('You must upload a picture')
#         if not picture.content_type or not picture.content_type.startswith('image'):
#             raise forms.ValidationError('File type is not image')
#         if picture.size > MAX_UPLOAD_SIZE:
#             raise forms.ValidationError('File too big (max size is {} bytes)'.format(MAX_UPLOAD_SIZE))
#         return picture

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']
        widgets = {
            # 'bio': forms.Textarea(attrs={'id':'id_bio_input_text', 'cols': 30, 'rows':'3'}),
            'profile_picture': forms.FileInput(attrs={'id': 'id_profile_picture'})
        }
        labels = {
            'bio': "Bio",
            'profile_picture': "Upload image"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['bio'].initial = self.instance.bio
            self.fields['profile_picture'].initial = self.instance.profile_picture

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if not hasattr(picture, 'content_type'):
                raise forms.ValidationError('You must upload a picture')
            if not picture.content_type or not picture.content_type.startswith('image'):
                raise forms.ValidationError('File type is not image')
            if picture.size > MAX_UPLOAD_SIZE:
                raise forms.ValidationError('File too big (max size is {} bytes)'.format(MAX_UPLOAD_SIZE))
        return picture

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        return bio


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'image', 'text', 'latitude', 'longitude') # 'x', 'y', 'width', 'height', 'scaleX', 'scaleY')
        widgets = {
                'title': forms.TextInput(attrs={'cols': 20, 'required':'required'}),
                'image': forms.FileInput(attrs={'value': 'Choose file', 'onchange': "loadFile(event), 'required':'required'"}),
                'text': forms.Textarea(attrs={'cols': 20, 'required':'required'}),
                'latitude': forms.HiddenInput(attrs={'required':'required'}),
                'longitude': forms.HiddenInput(attrs={'required':'required'}),
                # 'x': forms.HiddenInput(attrs={}),
                # 'y': forms.HiddenInput(attrs={}),
                # 'width': forms.HiddenInput(attrs={}),
                # 'height': forms.HiddenInput(attrs={}),
                # 'scaleX': forms.HiddenInput(attrs={}),
                # 'scaleY': forms.HiddenInput(attrs={}),
        }

        labels = {
            'title': "title",
            'text': "description"
        }

    def clean_picture(self):
        image = self.cleaned_data['image']
        if not image or not hasattr(image, 'content_type'):
            return image
        if not image.content_type or not image.content_type.startswith('image'):
            raise forms.ValidationError('File type is not image')
        if image.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError('File too big')
        return image

class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Playlist Name'}),
        }
