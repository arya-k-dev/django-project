from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile
import json

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    pass

class ProfileUpdateForm(forms.ModelForm):
    # JSON field for timeline milestones (display as textarea)
    timeline_milestones_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': '[{"date": "Jan 2026", "text": "Joined SkillSwap"}]'}),
        required=False,
        label="Learning journey milestones (JSON)"
    )

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar', 'location', 'availability', 'linkedin_url', 'website_url',
            'response_rate', 'available_slots', 'timeline_milestones_json'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'available_slots': forms.Textarea(attrs={'rows': 2}),
            'response_rate': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        # Accept and remove 'user' argument if passed (from views)
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Make response_rate optional since it has a default value
        self.fields['response_rate'].required = False
        # Make available_slots optional since it's blank=True
        self.fields['available_slots'].required = False
        # Pre-populate JSON text field if instance has timeline_milestones
        if self.instance and self.instance.timeline_milestones:
            self.initial['timeline_milestones_json'] = json.dumps(self.instance.timeline_milestones, indent=2)
        else:
            self.initial['timeline_milestones_json'] = ''

    def clean_timeline_milestones_json(self):
        timeline_json = self.cleaned_data.get('timeline_milestones_json', '').strip()
        if not timeline_json:
            return ''
        
        try:
            json.loads(timeline_json)
        except json.JSONDecodeError:
            raise forms.ValidationError('Invalid JSON format. Please use valid JSON syntax.')
        
        return timeline_json

    def save(self, commit=True):
        instance = super().save(commit=False)
        timeline_json = self.cleaned_data.get('timeline_milestones_json')
        if timeline_json:
            try:
                instance.timeline_milestones = json.loads(timeline_json)
            except json.JSONDecodeError:
                instance.timeline_milestones = []
        else:
            instance.timeline_milestones = []
        if commit:
            instance.save()
        return instance