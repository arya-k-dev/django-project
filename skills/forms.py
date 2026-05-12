from django import forms
from .models import UserSkill, Skill, SkillCategory


class UserSkillForm(forms.ModelForm):
    skill_name = forms.CharField(
        max_length=100,
        required=False,
        label='Skill name',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'autocomplete': 'off',
            'placeholder': 'Start typing a skill...',
        }),
    )

    class Meta:
        model = UserSkill
        fields = ('skill', 'skill_name', 'skill_type', 'level', 'years_experience', 'description')
        widgets = {
            'skill': forms.HiddenInput(),
            'skill_type': forms.HiddenInput(),
            'level': forms.Select(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 50}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['skill'].required = False
        if self.instance and self.instance.pk and self.instance.skill_id:
            self.fields['skill_name'].initial = self.instance.skill.name

    def clean(self):
        cleaned_data = super().clean()
        skill = cleaned_data.get('skill')
        skill_name = (cleaned_data.get('skill_name') or '').strip()

        if not skill and skill_name:
            skill_obj = Skill.objects.filter(name__iexact=skill_name).first()
            if not skill_obj:
                skill_obj = Skill.objects.create(name=skill_name)
            cleaned_data['skill'] = skill_obj
        elif not skill:
            raise forms.ValidationError('Please select or enter a skill.')
        return cleaned_data


class SkillSearchForm(forms.Form):
    query = forms.CharField(max_length=100, required=False, label='Search Skills',
                            widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Search skills...'}))
    category = forms.ModelChoiceField(queryset=SkillCategory.objects.all(), required=False,
                                      widget=forms.Select(attrs={'class': 'form-input'}))
