from django.contrib.auth.models import Group
from app.models import Student

def user_roles(request):
    """
    Context processor to provide role details to all templates.
    Roles: 'admin', 'trainer', 'student'
    """
    if not request.user.is_authenticated:
        return {
            'user_role': 'anonymous',
            'is_admin_role': False,
            'is_trainer_role': False,
            'is_student_role': False,
            'role_display': 'Guest',
            'current_student': None,
        }

    user = request.user

    # Determine real role
    if user.is_superuser:
        real_role = 'admin'
    else:
        group_names = set(user.groups.values_list('name', flat=True))
        if 'Teacher' in group_names or 'Trainer' in group_names or user.trainer_batches.exists() or user.trainer_courses.exists():
            real_role = 'trainer'
        elif user.is_staff or 'Counsellor' in group_names or 'Project Coordinator' in group_names or 'Admin' in group_names:
            real_role = 'admin'
        else:
            real_role = 'student'

    # Admin/Staff can preview different roles via ?view_as=
    view_as = request.GET.get('view_as')
    if (user.is_superuser or user.is_staff) and view_as in ['admin', 'trainer', 'student']:
        active_role = view_as
    else:
        active_role = real_role

    role_labels = {
        'admin': 'Administrator' if user.is_superuser else 'Staff / Counsellor',
        'trainer': 'Trainer / Faculty',
        'student': 'Student / Learner',
    }

    # Find associated Student model instance if any
    student_profile = None
    if hasattr(user, 'student_profile') and user.student_profile:
        student_profile = user.student_profile
    else:
        student_profile = Student.objects.filter(email__iexact=user.email).first()

    return {
        'user_role': active_role,
        'real_user_role': real_role,
        'is_admin_role': active_role == 'admin',
        'is_trainer_role': active_role == 'trainer',
        'is_student_role': active_role == 'student',
        'role_display': role_labels.get(active_role, 'User'),
        'current_student': student_profile,
    }

