
 if user.role != 'doctor':
            raise serializers.ValidationError(
                "This login is for doctors only. You don't have doctor access."
            )
        
        