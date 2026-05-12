from django import forms

from .models import Rating


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ('score', 'teaching_quality', 'communication', 'punctuality', 'feedback')
        widgets = {
            'score': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'teaching_quality': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'communication': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'punctuality': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'feedback': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-input',
                'placeholder': 'Share your experience...',
            }),
        }
