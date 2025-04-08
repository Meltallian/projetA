# game/forms.py
from django import forms
from .models import PlayerProfile, GameSession, Player

class PlayerVerificationForm(forms.Form):
    name = forms.CharField(max_length=100, label="Your Name")
    verification_code = forms.CharField(
        max_length=4, 
        min_length=4, 
        label="4-Digit Verification Code",
        widget=forms.PasswordInput(attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        code = cleaned_data.get('verification_code')
        
        if name and code:
            try:
                PlayerProfile.objects.get(name=name, verification_code=code)
            except PlayerProfile.DoesNotExist:
                raise forms.ValidationError("Invalid name or verification code.")
        
        return cleaned_data

class GameMasterRegistrationForm(forms.ModelForm):
    verification_code = forms.CharField(
        max_length=4, 
        min_length=4,
        widget=forms.PasswordInput(attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'})
    )
    
    class Meta:
        model = PlayerProfile
        fields = ['name', 'verification_code']
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.is_game_master = True
        if commit:
            profile.save()
        return profile

class PlayerRegistrationForm(forms.ModelForm):
    verification_code = forms.CharField(
        max_length=4, 
        min_length=4,
        widget=forms.PasswordInput(attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'})
    )
    
    class Meta:
        model = PlayerProfile
        fields = ['name', 'verification_code']