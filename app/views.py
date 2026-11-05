
from io import BytesIO
from uuid import uuid4

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from .forms import AdmissionReportFilterForm
from .forms import AdmissionSettingsForm
from .models import AdmissionSettings
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from .models import (
    Admission,
    AdmissionDocument,
    AdmissionStatusHistory,
)

from decimal import Decimal
from .models import Enquiry
from .forms import EnquiryForm
from .forms import ExaminationMarkForm
from .models import ExaminationMark
from .models import ExamCentre
from .forms import ExamCentreForm
from .models import CounsellingRecord
from .forms import CounsellingRecordForm

from .models import (
    Admission,
    AdmissionDocument,
    AdmissionStatusHistory,
    AdmissionConfirmation,
)

from .forms import (
    AdmissionRegistrationForm,
    DocumentVerificationForm,
)
from .models import Course
from .models import Batch

from django.db.models import F
from django.core.exceptions import FieldDoesNotExist
from .models import FeeStructure, FeeInstallment, FeePayment, Invoice
from .forms import (
    FeeStructureForm,
    FeeInstallmentForm,
    FeePaymentForm,
    InvoiceForm,
)

from .forms import (
    DiplomaExamRegistrationForm,
    EligibilityVerificationForm,
    PaymentVerificationForm,
    ExaminationCentreForm
)
from .models import (
    DiplomaExam,
    DiplomaExamEligibility,
    DiplomaExamPayment,
    DiplomaExamRegistration,
    ExaminationCentre,
    Examination,
    ExaminationSubject,
    ExamApplication,
    ExamApplicationPayment,
    HallTicket,
    ExaminationMark,
    ExaminationResult,
    Certificate,
    Student,
    Course,
)
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Admission
from .forms import OutstandingFeesFilterForm
from .forms import ExamFeePaymentForm
from .models import ExamFeePayment
from .models import FeeReminder, Admission
from .forms import FeeReminderForm, FeeReminderFilterForm
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from .forms import ExaminationResultFilterForm
from .forms import (
    DiplomaExamRegistrationForm, EligibilityVerificationForm,
    PaymentVerificationForm, ExaminationForm, ExaminationCentreForm,
    ExaminationSubjectForm,
)
from .models import (
    DiplomaExam, DiplomaExamEligibility, DiplomaExamRegistration,
    DiplomaExamPayment, Examination, ExaminationCentre, ExaminationSubject,
    ExamApplication, ExamApplicationPayment, HallTicket, ExaminationMark,
    ExaminationResult, Certificate,
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .models import HallTicket
from .forms import HallTicketForm

from .models import ExamSchedule
from .forms import ExamScheduleForm

User = get_user_model()


# ==========================================================
# PUBLIC / MARKETING VIEWS
# ==========================================================

def home(request):
    return render(request, "home.html")


def features(request):
    return render(request, "features.html")


def about(request):
    return render(request, "about.html")


def benefits(request):
    return render(request, "benefits.html")


def faq(request):
    return render(request, "faq.html")


def contact(request):
    if request.method == "POST":
        messages.success(
            request,
            "Thank you! Your message has been received."
        )
        return redirect("contact")

    return render(request, "contact.html")


# ==========================================================
# USER REGISTRATION
# ==========================================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect("admission_dashboard")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        terms = request.POST.get("terms")

        if not all([
            first_name,
            last_name,
            email,
            password,
            confirm_password,
        ]):
            messages.error(
                request,
                "Please fill in all required fields."
            )
            return render(request, "register.html")

        if not terms:
            messages.error(
                request,
                "Please accept the Terms of Service."
            )
            return render(request, "register.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(
                request,
                "Please enter a valid email address."
            )
            return render(request, "register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        if User.objects.filter(email__iexact=email).exists():
            messages.error(
                request,
                "An account with this email already exists."
            )
            return render(request, "register.html")

        try:
            validate_password(password)

            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )

                student_group, _ = Group.objects.get_or_create(
                    name="Student"
                )
                user.groups.add(student_group)

            messages.success(
                request,
                "Registration successful! Please sign in."
            )
            return redirect("login")

        except ValidationError as error:
            for error_message in error.messages:
                messages.error(request, error_message)

        except IntegrityError:
            messages.error(
                request,
                "An account with these details already exists."
            )

    return render(request, "register.html")


# ==========================================================
# USER LOGIN
# ==========================================================

def login_view(request):
    next_url = (
        request.POST.get("next")
        or request.GET.get("next", "")
    )

    if request.user.is_authenticated:
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        return redirect("admission_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(
                request,
                "Please enter your email/username and password."
            )
            return render(
                request,
                "login.html",
                {"next": next_url},
            )

        user_identifier = username

        if "@" in username:
            matching_user = User.objects.filter(
                email__iexact=username
            ).first()

            if matching_user:
                user_identifier = matching_user.get_username()

        user = authenticate(
            request,
            username=user_identifier,
            password=password,
        )

        if user is None:
            messages.error(
                request,
                "Invalid email/username or password."
            )
            return render(
                request,
                "login.html",
                {"next": next_url},
            )

        auth_login(request, user)

        messages.success(
            request,
            f"Welcome back, {user.first_name or user.get_username()}!"
        )

        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        return redirect("admission_dashboard")

    return render(
        request,
        "login.html",
        {"next": next_url},
    )


# ==========================================================
# USER LOGOUT
# ==========================================================

def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
        messages.success(
            request,
            "You have been logged out successfully."
        )
        return redirect("home")

    return redirect("home")


# ==========================================================
# ADMISSION DASHBOARD
# ==========================================================
@login_required(login_url="login")
def admission_dashboard(request):
    today = timezone.localdate()

    # Total enquiries
    total_enquiries = Enquiry.objects.count()

    # Follow-ups due today or overdue
    pending_followups = Enquiry.objects.filter(
        followup_date__lte=today,
        status__in=[
            "New",
            "Contacted",
            "Counselling Completed",
            "Interested",
            "Follow-up",
        ],
    ).count()

    # Ongoing counselling records
    ongoing_counselling = CounsellingRecord.objects.filter(
        counselling_status__in=[
            "New",
            "Contacted",
            "Interested",
            "Follow-up",
        ]
    ).count()

    # Confirmed admissions
    confirmed_admissions = Admission.objects.filter(
        admission_status="Confirmed"
    ).count()

    # Admissions created for today's date
    today_admissions = Admission.objects.filter(
        admission_date=today
    ).count()

    # Most recent enquiries
    recent_enquiries = Enquiry.objects.select_related(
        "course_interested",
        "assigned_counsellor",
    ).order_by("-enquiry_date", "-created_at")[:8]

    # Enquiries grouped by lead source
    lead_sources = list(
        Enquiry.objects.values("lead_source")
        .annotate(count=Count("id"))
        .order_by("lead_source")
    )

    context = {
        "today": today,
        "total_enquiries": total_enquiries,
        "pending_followups": pending_followups,
        "ongoing_counselling": ongoing_counselling,
        "confirmed_admissions": confirmed_admissions,
        "today_admissions": today_admissions,
        "recent_enquiries": recent_enquiries,
        "lead_sources": lead_sources,
    }

    return render(
        request,
        "admissions/admission_dashboard.html",
        context,
    )



@login_required
def enquiry_management(request):
    """
    Display enquiries and allow users to search existing records.
    """
    enquiries = Enquiry.objects.select_related(
        "course_interested",
        "assigned_counsellor",
    ).order_by("-enquiry_date", "-created_at")

    search_query = request.GET.get("q", "").strip()

    if search_query:
        enquiries = enquiries.filter(
            Q(student_name__icontains=search_query)
            | Q(mobile__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(college__icontains=search_query)
            | Q(location__icontains=search_query)
            | Q(enquiry_id__icontains=search_query)
        )

    context = {
        "enquiries": enquiries,
        "search_query": search_query,
        "total_enquiries": Enquiry.objects.count(),
        "form": EnquiryForm(),
    }

    return render(
        request,
        "admissions/enquiry_management.html",
        context,
    )


@login_required
def enquiry_create(request):
    """
    Validate and save a new enquiry.
    """
    if request.method == "POST":
        form = EnquiryForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Enquiry added successfully.",
            )
            return redirect("enquiry_management")

        messages.error(
            request,
            "Please correct the errors in the enquiry form.",
        )
    else:
        form = EnquiryForm()

    return render(
        request,
        "admissions/enquiry_form.html",
        {
            "form": form,
            "page_title": "Add New Enquiry",
            "button_text": "Save Enquiry",
        },
    )


@login_required
def enquiry_edit(request, pk):
    """
    Edit an existing enquiry.
    """
    enquiry = get_object_or_404(Enquiry, pk=pk)

    if request.method == "POST":
        form = EnquiryForm(request.POST, instance=enquiry)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Enquiry updated successfully.",
            )
            return redirect("enquiry_management")

        messages.error(
            request,
            "Please correct the errors in the enquiry form.",
        )
    else:
        form = EnquiryForm(instance=enquiry)

    return render(
        request,
        "admissions/enquiry_form.html",
        {
            "form": form,
            "enquiry": enquiry,
            "page_title": "Edit Enquiry",
            "button_text": "Update Enquiry",
        },
    )


@login_required
def enquiry_delete(request, pk):
    """
    Delete an enquiry only after a POST confirmation.
    """
    enquiry = get_object_or_404(Enquiry, pk=pk)

    if request.method == "POST":
        enquiry.delete()
        messages.success(
            request,
            "Enquiry deleted successfully.",
        )
        return redirect("enquiry_management")

    return render(
        request,
        "admissions/enquiry_confirm_delete.html",
        {"enquiry": enquiry},
    )

@login_required
def counselling_management(request):
    records = CounsellingRecord.objects.select_related(
        "enquiry",
        "counsellor",
        "recommended_course",
    )

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        records = records.filter(
            Q(enquiry__student_name__icontains=search_query)
            | Q(enquiry__mobile__icontains=search_query)
            | Q(enquiry__email__icontains=search_query)
            | Q(counsellor__username__icontains=search_query)
            | Q(recommended_course__name__icontains=search_query)
            | Q(counselling_status__icontains=search_query)
        )

    if status_filter:
        records = records.filter(
            counselling_status=status_filter
        )

    context = {
        "counselling_records": records,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": CounsellingRecord.STATUS_CHOICES,
        "total_counselling": CounsellingRecord.objects.count(),
    }

    return render(
        request,
        "admissions/counselling_management.html",
        context,
    )


@login_required
def counselling_create(request):
    if request.method == "POST":
        form = CounsellingRecordForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Counselling record added successfully.",
            )
            return redirect("counselling_management")
    else:
        form = CounsellingRecordForm(
            initial={"counsellor": request.user}
        )

    return render(
        request,
        "admissions/counselling_form.html",
        {
            "form": form,
            "page_title": "Add Counselling Record",
            "button_text": "Save Counselling",
        },
    )


@login_required
def counselling_edit(request, pk):
    record = get_object_or_404(
        CounsellingRecord,
        pk=pk,
    )

    if request.method == "POST":
        form = CounsellingRecordForm(
            request.POST,
            instance=record,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Counselling record updated successfully.",
            )
            return redirect("counselling_management")
    else:
        form = CounsellingRecordForm(instance=record)

    return render(
        request,
        "admissions/counselling_form.html",
        {
            "form": form,
            "record": record,
            "page_title": "Edit Counselling Record",
            "button_text": "Update Counselling",
        },
    )


@login_required
def counselling_delete(request, pk):
    record = get_object_or_404(
        CounsellingRecord,
        pk=pk,
    )

    if request.method == "POST":
        record.delete()
        messages.success(
            request,
            "Counselling record deleted successfully.",
        )
        return redirect("counselling_management")

    return render(
        request,
        "admissions/counselling_confirm_delete.html",
        {"record": record},
    )



@login_required
def admission_registration(request):
    if request.method == "POST":
        form = AdmissionRegistrationForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            data = form.cleaned_data

            try:
                with transaction.atomic():
                    # Create the student profile.
                    student = Student(
                        full_name=data["full_name"],
                        email=data["email"],
                        mobile=data["mobile"],
                        dob=data.get("dob"),
                        gender=data.get("gender") or "",
                        address=data.get("address") or "",
                        location=data.get("location") or "",
                        highest_qualification=(
                            data.get("highest_qualification") or ""
                        ),
                        university=data.get("university") or "",
                        college=data.get("college") or "",
                        passing_year=data.get("passing_year"),
                        percentage_cgpa=(
                            data.get("percentage_cgpa") or ""
                        ),
                        photo=data.get("photo"),
                    )
                    student.save()

                    course = data["course"]
                    batch = data.get("batch")
                    previous_status = "Draft"

                    # Save admission and calculate the fees
                    # using the actual course fee.
                    admission = Admission(
                        enquiry=data.get("enquiry_id"),
                        student=student,
                        course=course,
                        batch=batch,
                        delivery_mode=data["delivery_mode"],
                        admission_date=data["admission_date"],
                        course_fee=Decimal(str(course.fee or "0.00")),
                        scholarship_discount=(
                            data.get("scholarship_discount")
                            or Decimal("0.00")
                        ),
                        amount_paid=(
                            data.get("amount_paid")
                            or Decimal("0.00")
                        ),
                        admission_status="Documents Pending",
                        counsellor=request.user,
                        remarks=data.get("remarks") or "",
                    )

                    admission.full_clean()
                    admission.save()

                    # Create a record for every document type.
                    # Missing documents remain "Not Uploaded".
                    document_fields = [
                        (
                            "Student Photo",
                            "photo",
                        ),
                        (
                            "Identity Proof",
                            "doc_id_proof",
                        ),
                        (
                            "Educational Certificate",
                            "doc_education",
                        ),
                        (
                            "Resume",
                            "doc_resume",
                        ),
                        (
                            "Other Documents",
                            "doc_other",
                        ),
                    ]

                    for document_name, field_name in document_fields:
                        uploaded_file = (
                            data.get(field_name)
                            if field_name != "photo"
                            else None
                        )

                        if (
                            document_name == "Student Photo"
                            and student.photo
                        ):
                            # Store a document record for the photo.
                            # The image itself remains Student.photo.
                            document_status = "Pending Verification"
                        elif uploaded_file:
                            document_status = "Pending Verification"
                        else:
                            document_status = "Not Uploaded"

                        document = AdmissionDocument(
                            admission=admission,
                            document_name=document_name,
                            document_file=uploaded_file,
                            is_mandatory=True,
                            verification_status=document_status,
                        )

                        document.save()

                    AdmissionStatusHistory.objects.create(
                        admission=admission,
                        previous_status=previous_status,
                        new_status="Documents Pending",
                        remarks="Admission registration created.",
                        changed_by=request.user,
                    )

                messages.success(
                    request,
                    (
                        f"Registration successful. "
                        f"Admission Number: {admission.admission_number}. "
                        f"Student ID: {student.student_id}."
                    ),
                )

                return redirect(
                    "admission_detail",
                    pk=admission.pk,
                )

            except (ValidationError, IntegrityError) as exc:
                if isinstance(exc, ValidationError):
                    if hasattr(exc, "message_dict"):
                        for field, errors in exc.message_dict.items():
                            for error in errors:
                                form.add_error(
                                    field if field in form.fields else None,
                                    error,
                                )
                    else:
                        for error in exc.messages:
                            form.add_error(None, error)
                else:
                    form.add_error(
                        None,
                        "Registration could not be saved. Please try again.",
                    )

                messages.error(
                    request,
                    "Please correct the errors below.",
                )

    else:
        form = AdmissionRegistrationForm()

    return render(
        request,
        "admissions/admission_registration.html",
        {"form": form},
    )


@login_required
def admission_register(request):
    admissions = Admission.objects.select_related(
        "student",
        "course",
        "batch",
        "counsellor",
    ).order_by("-created_at")

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        from django.db.models import Q

        admissions = admissions.filter(
            Q(admission_number__icontains=search)
            | Q(student__student_id__icontains=search)
            | Q(student__full_name__icontains=search)
            | Q(student__email__icontains=search)
            | Q(course__name__icontains=search)
        )

    valid_statuses = {
        value for value, label
        in Admission.ADMISSION_STATUS_CHOICES
    }

    if status in valid_statuses:
        admissions = admissions.filter(admission_status=status)

    return render(
        request,
        "admissions/admission_list.html",
        {
            "admissions": admissions,
            "search": search,
            "selected_status": status,
            "status_choices": Admission.ADMISSION_STATUS_CHOICES,
        },
    )


@login_required
def admission_detail(request, pk):
    admission = get_object_or_404(
        Admission.objects.select_related(
            "student",
            "course",
            "batch",
            "counsellor",
        ).prefetch_related("documents", "status_history"),
        pk=pk,
    )

    return render(
        request,
        "admissions/admission_detail.html",
        {"admission": admission},
    )


@login_required
def document_verification(request, pk):
    admission = get_object_or_404(Admission, pk=pk)

    if request.method == "POST":
        document_id = request.POST.get("document_id")

        document = get_object_or_404(
            AdmissionDocument,
            pk=document_id,
            admission=admission,
        )

        form = DocumentVerificationForm(
            request.POST,
            instance=document,
        )

        if form.is_valid():
            if not document.document_file and (
                document.document_name != "Student Photo"
                or not admission.student.photo
            ):
                form.add_error(
                    None,
                    "Upload the document before verifying it.",
                )
            else:
                verified_document = form.save(commit=False)

                if verified_document.verification_status == "Verified":
                    verified_document.verified_by = request.user
                    verified_document.verified_at = timezone.now()
                else:
                    verified_document.verified_by = None
                    verified_document.verified_at = None

                verified_document.save()

                messages.success(
                    request,
                    f"{document.document_name} verification updated.",
                )

                return redirect(
                    "document_verification",
                    pk=admission.pk,
                )
    else:
        form = DocumentVerificationForm()

    return render(
        request,
        "admissions/document_verification.html",
        {
            "admission": admission,
            "documents": admission.documents.all(),
            "form": form,
        },
    )


@login_required
def admission_confirmation(request, pk):
    admission = get_object_or_404(
        Admission.objects.select_related("student", "course"),
        pk=pk,
    )

    if request.method == "POST":
        if admission.admission_status == "Cancelled":
            messages.error(
                request,
                "A cancelled admission cannot be confirmed.",
            )
            return redirect("admission_detail", pk=admission.pk)

        if admission.admission_status == "Confirmed":
            messages.info(request, "This admission is already confirmed.")
            return redirect("admission_detail", pk=admission.pk)

        if not admission.all_mandatory_documents_verified:
            messages.error(
                request,
                "Verify all mandatory documents before confirmation.",
            )
            return redirect("document_verification", pk=admission.pk)

        with transaction.atomic():
            previous_status = admission.admission_status
            admission.admission_status = "Confirmed"
            admission.save()

            AdmissionConfirmation.objects.get_or_create(
                admission=admission,
                defaults={
                    "confirmed_by": request.user,
                    "remarks": "Admission confirmed after document verification.",
                },
            )

            AdmissionStatusHistory.objects.create(
                admission=admission,
                previous_status=previous_status,
                new_status="Confirmed",
                remarks="Admission confirmed.",
                changed_by=request.user,
            )

        messages.success(
            request,
            f"Admission {admission.admission_number} confirmed successfully.",
        )

        return redirect("admission_detail", pk=admission.pk)

    return render(
        request,
        "admissions/admission_confirmation.html",
        {"admission": admission},
    )


@login_required
def student_list(request):
    search = request.GET.get("q", "").strip()

    students = Student.objects.all()

    if search:
        students = students.filter(
            Q(full_name__icontains=search)
            | Q(student_id__icontains=search)
            | Q(email__icontains=search)
            | Q(mobile__icontains=search)
        )

    paginator = Paginator(students.order_by("full_name"), 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "admissions/student_list.html",
        {
            "students": page_obj.object_list,
            "page_obj": page_obj,
            "search_query": search,
        },
    )


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)

    admissions = Admission.objects.filter(
        student=student
    ).select_related(
        "course",
        "batch",
    ).order_by("-created_at")

    return render(
        request,
        "admissions/student_profile.html",
        {
            "student": student,
            "admissions": admissions,
        },
    )
@login_required
def admission_reports(request):
    filter_form = AdmissionReportFilterForm(request.GET or None)

    admissions = Admission.objects.select_related(
        "student", "course", "batch"
    )

    if filter_form.is_valid():
        search = filter_form.cleaned_data.get("search", "").strip()
        status = filter_form.cleaned_data.get("status", "")

        if search:
            admissions = admissions.filter(
                Q(student__full_name__icontains=search)
                | Q(admission_number__icontains=search)
            )

        if status:
            admissions = admissions.filter(
                admission_status__iexact=status
            )

    total_students = Student.objects.count()
    total_admissions = Admission.objects.count()

    confirmed_admissions = Admission.objects.filter(
        admission_status__iexact="Confirmed"
    ).count()

    pending_admissions = Admission.objects.filter(
        admission_status__iexact="Pending"
    ).count()

    course_report = (
        admissions.values("course__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    recent_admissions = admissions.order_by("-created_at")[:10]

    context = {
        "filter_form": filter_form,
        "total_students": total_students,
        "total_admissions": total_admissions,
        "confirmed_admissions": confirmed_admissions,
        "pending_admissions": pending_admissions,
        "course_report": course_report,
        "recent_admissions": recent_admissions,
    }

    return render(
        request,
        "admissions/admission_reports.html",
        context,
    )

@login_required
def admission_settings(request):
    settings_obj, created = AdmissionSettings.objects.get_or_create(
        pk=1,
        defaults={
            "institution_name": "SciPy Technologies",
            "admission_number_prefix": "SC-ADM",
            "default_admission_status": "Pending",
            "require_document_verification": True,
        },
    )

    if request.method == "POST":
        form = AdmissionSettingsForm(
            request.POST,
            instance=settings_obj,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Admission settings saved successfully.",
            )

            return redirect("admission_settings")

        messages.error(
            request,
            "Please correct the errors below and try again.",
        )

    else:
        form = AdmissionSettingsForm(instance=settings_obj)

    return render(
        request,
        "admissions/admission_settings.html",
        {
            "form": form,
            "settings_obj": settings_obj,
        },
    )



@login_required
def scheduling_dashboard(request):
    context = {
        "total_courses": 0,
        "active_batches": 0,
        "total_trainers": 0,
        "upcoming_sessions": 0,
    }

    return render(
        request,
        "admissions/scheduling.html",
        context,
    )



@login_required
def course_list(request):
    courses = (
        Course.objects
        .filter(status="Active")
        .select_related("category", "assigned_trainer")
        .order_by("name")
    )

    context = {
        "courses": courses,
        "total_courses": courses.count(),
    }

    return render(
        request,
        "admissions/course_list.html",
        context,
    )


@login_required
def batch_list(request):
    batches = list(
        Batch.objects
        .select_related(
            "course",
            "course__category",
            "assigned_trainer",
        )
        .order_by("-start_date")
    )

    for batch in batches:
        if batch.max_capacity > 0:
            batch.capacity_percentage = min(
                100,
                round(
                    batch.current_student_count
                    * 100
                    / batch.max_capacity
                ),
            )
        else:
            batch.capacity_percentage = 0

    context = {
        "batches": batches,
        "total_batches": len(batches),
    }

    return render(
        request,
        "admissions/batch_list.html",
        context,
    )





@login_required(login_url="login")
def fee_dashboard(request):
    today = timezone.localdate()

    installments = FeeInstallment.objects.all()

    # Outstanding-fee filters
    student = request.GET.get("student", "").strip()
    course = request.GET.get("course", "").strip()
    batch = request.GET.get("batch", "").strip()
    counsellor = request.GET.get("counsellor", "").strip()
    due_date = request.GET.get("due_date", "").strip()
    payment_status = request.GET.get("payment_status", "").strip()

    if student:
        installments = installments.filter(student__icontains=student)

    if course:
        installments = installments.filter(course__icontains=course)

    if batch:
        installments = installments.filter(batch__icontains=batch)

    if counsellor:
        installments = installments.filter(
            counsellor__icontains=counsellor
        )

    if due_date:
        try:
            from datetime import date
            date.fromisoformat(due_date)
            installments = installments.filter(due_date__lte=due_date)
        except ValueError:
            due_date = ""

    if payment_status == "pending":
        installments = installments.filter(
            amount__gt=F("amount_paid"),
        ).filter(
            Q(due_date__gte=today) | Q(due_date__isnull=True)
        )
    elif payment_status == "overdue":
        installments = installments.filter(
            due_date__lt=today,
            amount__gt=F("amount_paid"),
        )

    # Financial summary
    total_receivable = (
        FeeInstallment.objects.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    total_collected = (
        FeePayment.objects.filter(status="active").aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    outstanding_amount = sum(
        (
            max(Decimal("0.00"), item.amount - item.amount_paid)
            for item in FeeInstallment.objects.all()
        ),
        Decimal("0.00"),
    )

    overdue_amount = sum(
        (
            max(Decimal("0.00"), item.amount - item.amount_paid)
            for item in FeeInstallment.objects.filter(
                due_date__lt=today,
                amount__gt=F("amount_paid"),
            )
        ),
        Decimal("0.00"),
    )

    context = {
        "today": today,
        "total_receivable": total_receivable,
        "total_collected": total_collected,
        "outstanding_amount": outstanding_amount,
        "overdue_amount": overdue_amount,
        "fee_structures": FeeStructure.objects.all().order_by("course"),
        "recent_installments": FeeInstallment.objects.all().order_by(
            "due_date", "-id"
        )[:10],
        "recent_payments": FeePayment.objects.select_related(
            "collected_by", "installment"
        ).order_by("-payment_date", "-id")[:10],
        "recent_invoices": Invoice.objects.all().order_by(
            "-invoice_date", "-id"
        )[:10],
        "outstanding_installments": installments.filter(
            amount__gt=F("amount_paid")
        ).order_by("due_date", "-id"),
        "filters": {
            "student": student,
            "course": course,
            "batch": batch,
            "counsellor": counsellor,
            "due_date": due_date,
            "payment_status": payment_status,
        },
    }

    return render(request, "admissions/fee_dashboard.html", context)


@login_required
def fee_structure_create(request):
    if request.method == "POST":
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee structure created successfully.")
            return redirect("fee_dashboard")
    else:
        form = FeeStructureForm()

    return render(
        request, "admissions/fee_structure_form.html", {"form": form}
    )

@login_required
def fee_installment_create(request):
    if request.method == "POST":
        form = FeeInstallmentForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Installment created successfully."
            )
            return redirect("fee_dashboard")
    else:
        form = FeeInstallmentForm()

    return render(
        request,
        "admissions/fee_installment_form.html",
        {"form": form},
    )


@login_required
def fee_payment_create(request):
    if request.method == "POST":
        form = FeePaymentForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.collected_by = request.user
                payment.status = "active"
                payment.save()

                # Keep the installment's paid total in sync with active payments.
                if payment.installment_id:
                    installment = FeeInstallment.objects.select_for_update().get(
                        pk=payment.installment_id
                    )
                    paid_total = (
                        installment.payments.filter(status="active").aggregate(
                            total=Sum("amount")
                        )["total"]
                        or Decimal("0.00")
                    )
                    installment.amount_paid = min(
                        installment.amount, paid_total
                    )
                    installment.save(update_fields=["amount_paid"])

            messages.success(
                request,
                f"Payment recorded. Receipt: {payment.receipt_number}",
            )
            return redirect("fee_dashboard")
    else:
        form = FeePaymentForm()

    return render(
        request, "admissions/fee_payment_form.html", {"form": form}
    )


@login_required
def fee_invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Invoice created successfully.")
            return redirect("fee_dashboard")
    else:
        form = InvoiceForm()

    return render(
        request, "admissions/fee_invoice_form.html", {"form": form}
    )


@login_required
def outstanding_fees(request):
    form = OutstandingFeesFilterForm(request.GET or None)

    # Read existing admission records; do not create payments here.
    admissions = (
        Admission.objects
        .select_related("student", "course")
        .filter(outstanding_balance__gt=0)
        .order_by("-outstanding_balance")
    )

    if form.is_valid():
        search = form.cleaned_data.get("search")
        minimum_balance = form.cleaned_data.get("minimum_balance")

        if search:
            admissions = admissions.filter(
                Q(student__full_name__icontains=search)
                | Q(student__student_id__icontains=search)
                | Q(admission_number__icontains=search)
                | Q(course__name__icontains=search)
            )

        if minimum_balance is not None:
            admissions = admissions.filter(
                outstanding_balance__gte=minimum_balance
            )

    # Calculate summary values from the filtered results.
    summary = admissions.aggregate(
        total_students=Count("pk"),
        total_outstanding=Sum("outstanding_balance"),
    )

    context = {
        "form": form,
        "outstanding_admissions": admissions,
        "total_students": summary["total_students"] or 0,
        "total_outstanding": (
            summary["total_outstanding"] or Decimal("0.00")
        ),
    }

    return render(
        request,
        "admissions/outstanding_fees.html",
        context,
    )


@login_required
@require_http_methods(["GET", "POST"])
def fee_reminders(request):

    # Create a new reminder or update an existing reminder's status.
    if request.method == "POST":

        action = request.POST.get("action", "create")

        if action == "update_status":
            reminder = get_object_or_404(
                FeeReminder,
                pk=request.POST.get("reminder_id"),
            )

            new_status = request.POST.get("status")

            allowed_statuses = {
                value for value, label in FeeReminder.STATUS_CHOICES
            }

            if new_status not in allowed_statuses:
                messages.error(request, "Please select a valid status.")

            elif (
                new_status == FeeReminder.STATUS_COMPLETED
                and reminder.outstanding_balance > 0
            ):
                messages.error(
                    request,
                    "This reminder cannot be completed while "
                    "an outstanding fee balance remains. "
                    "Check the existing payment records first.",
                )

            else:
                reminder.status = new_status
                reminder.save(update_fields=["status", "updated_at"])

                messages.success(
                    request,
                    "Fee reminder status updated successfully.",
                )

            return redirect("fee_reminders")

        form = FeeReminderForm(request.POST)

        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.created_by = request.user
            reminder.save()

            messages.success(
                request,
                "Fee reminder created successfully.",
            )

            return redirect("fee_reminders")

        # Keep invalid form data visible on the page.
        filter_form = FeeReminderFilterForm(request.GET or None)

    else:
        form = FeeReminderForm()
        filter_form = FeeReminderFilterForm(request.GET or None)

    reminders = (
        FeeReminder.objects
        .select_related(
            "admission",
            "admission__student",
            "admission__course",
        )
        .all()
    )

    if filter_form.is_valid():
        search = filter_form.cleaned_data.get("search", "").strip()
        selected_status = filter_form.cleaned_data.get("status")

        if search:
            reminders = reminders.filter(
                Q(admission__student__full_name__icontains=search)
                | Q(admission__student__student_id__icontains=search)
                | Q(admission__admission_number__icontains=search)
                | Q(admission__course__name__icontains=search)
            )

        if selected_status:
            reminders = reminders.filter(status=selected_status)

    # Summary counts are based on the currently filtered records.
    summary = reminders.aggregate(
        total_reminders=Sum(
            # Count is calculated separately below.
            "admission__outstanding_balance"
        )
    )

    total_reminders = reminders.count()

    pending_count = reminders.filter(
        status=FeeReminder.STATUS_PENDING
    ).count()

    sent_count = reminders.filter(
        status=FeeReminder.STATUS_SENT
    ).count()

    overdue_count = sum(
        1 for reminder in reminders if reminder.is_overdue
    )

    context = {
        "form": form,
        "filter_form": filter_form,
        "reminders": reminders,
        "total_reminders": total_reminders,
        "pending_count": pending_count,
        "sent_count": sent_count,
        "overdue_count": overdue_count,
    }

    return render(
        request,
        "admissions/fee_reminders.html",
        context,
    )


def examination_staff_check(user):
    # Replace/extend this check with your project's role-based permission system.
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required(login_url="login")
def exam_application_dashboard(request):
    today = timezone.localdate()
    recent_qs = (
        ExamApplication.objects.select_related(
            "student", "examination", "examination__course"
        ).order_by("-created_at")[:10]
    )
    recent_applications = []
    for app in recent_qs:
        try:
            payment_status = app.examapplicationpayment.status
        except ExamApplicationPayment.DoesNotExist:
            payment_status = "Pending"
        recent_applications.append({
            "student_name": app.student.full_name,
            "student_id": app.student.student_id,
            "registration_number": app.registration_number,
            "diploma_name": app.examination.course.name,
            "eligibility_status": app.eligibility_status,
            "payment_status": payment_status,
            "status": app.status,
        })

    exams = Examination.objects.filter(
        exam_date__gte=today, status__in=["Open", "Closed", "Ongoing"]
    ).select_related("course", "centre").order_by("exam_date")[:10]
    upcoming_exams = [{
        "exam_name": e.exam_name,
        "exam_date": e.exam_date,
        "diploma_name": e.course.name,
        "exam_time": (
            f"{e.start_time.strftime('%I:%M %p')} - {e.end_time.strftime('%I:%M %p')}"
            if e.start_time and e.end_time else None
        ),
        "exam_centre": e.centre.name if e.centre else None,
        "exam_mode": e.exam_mode,
        "status": e.status,
    } for e in exams]

    context = {
        "total_applications": ExamApplication.objects.count(),
        "pending_applications": ExamApplication.objects.filter(status="Pending").count(),
        "hall_tickets_generated": HallTicket.objects.filter(status="Active").count(),
        "published_results": ExaminationResult.objects.filter(publication_status="Published").count(),
        "recent_applications": recent_applications,
        "upcoming_exams": upcoming_exams,
        "examinations": Examination.objects.select_related("course", "centre").all()[:20],
        "subjects": ExaminationSubject.objects.select_related("examination").all()[:30],
        "centres": ExaminationCentre.objects.filter(is_active=True),
        "hall_tickets": HallTicket.objects.select_related("application", "application__student", "application__examination").all()[:20],
        "marks": ExaminationMark.objects.select_related("application", "subject").all()[:20],
        "results": ExaminationResult.objects.select_related("application", "application__student", "application__examination").all()[:20],
        "certificates": Certificate.objects.select_related("student", "course", "exam_result").all()[:20],
        "examination_form": ExaminationForm(),
        "centre_form": ExaminationCentreForm(),
        "subject_form": ExaminationSubjectForm(),
    }
    return render(request, "admissions/exam_application.html", context)


@login_required
def examination_management(request):
    examinations = Examination.objects.all()

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        examinations = examinations.filter(
            Q(exam_code__icontains=search)
            | Q(exam_name__icontains=search)
            | Q(course_name__icontains=search)
            | Q(subject_name__icontains=search)
            | Q(exam_centre__icontains=search)
        )

    valid_statuses = {
        value for value, label in Examination.STATUS_CHOICES
    }

    if status in valid_statuses:
        examinations = examinations.filter(status=status)

    context = {
    "examinations": examinations,
    "total_count": Examination.objects.count(),
    "draft_count": Examination.objects.filter(status="Draft").count(),
    "scheduled_count": Examination.objects.filter(status="Scheduled").count(),
    "completed_count": Examination.objects.filter(status="Completed").count(),
    "search_query": search,
    "selected_status": status,
    "status_choices": Examination.STATUS_CHOICES,
}

    return render(
        request,
        "admissions/examination_management.html",
        context,
    )


@login_required
def examination_create(request):
    if request.method == "POST":
        form = ExaminationForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    examination = form.save(commit=False)
                    examination.full_clean()
                    examination.save()

                messages.success(
                    request,
                    "Examination created successfully.",
                )
                return redirect("examination_management")

            except IntegrityError:
                form.add_error(
                    "exam_code",
                    "This examination code already exists.",
                )

    else:
        form = ExaminationForm()

    return render(
        request,
        "admissions/examination_form.html",
        {
            "form": form,
            "page_title": "Create Examination",
            "button_text": "Save Examination",
        },
    )


@login_required
def examination_edit(request, exam_id):
    examination = get_object_or_404(
        Examination,
        pk=exam_id,
    )

    if request.method == "POST":
        form = ExaminationForm(
            request.POST,
            instance=examination,
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    updated_examination = form.save(commit=False)
                    updated_examination.full_clean()
                    updated_examination.save()

                messages.success(
                    request,
                    "Examination updated successfully.",
                )
                return redirect("examination_management")

            except IntegrityError:
                form.add_error(
                    "exam_code",
                    "This examination code already exists.",
                )

    else:
        form = ExaminationForm(instance=examination)

    return render(
        request,
        "admissions/examination_form.html",
        {
            "form": form,
            "page_title": "Edit Examination",
            "button_text": "Update Examination",
            "examination": examination,
        },
    )


@login_required
@require_POST
def examination_change_status(request, exam_id):
    examination = get_object_or_404(
        Examination,
        pk=exam_id,
    )

    new_status = request.POST.get("status", "").strip()
    valid_statuses = {
        value for value, label in Examination.STATUS_CHOICES
    }

    if new_status not in valid_statuses:
        messages.error(request, "Invalid examination status.")
        return redirect("examination_management")

    examination.status = new_status

    try:
        examination.full_clean()
        examination.save(update_fields=["status", "updated_at"])

        messages.success(
            request,
            f"Examination status changed to {new_status}.",
        )

    except Exception as exc:
        from django.core.exceptions import ValidationError

        if isinstance(exc, ValidationError):
            messages.error(request, "; ".join(exc.messages))
        else:
            raise

    return redirect("examination_management")


@login_required(login_url="login")
def diploma_exam_management(request):
    exams = DiplomaExam.objects.filter(is_active=True).order_by("exam_date")
    registrations = DiplomaExamRegistration.objects.filter(
        student=request.user
    ).select_related("exam").prefetch_related("payments")
    eligibility = {
        row.exam_id: row for row in DiplomaExamEligibility.objects.filter(
            student=request.user, exam__in=exams
        )
    }
    registration_by_exam = {row.exam_id: row for row in registrations}
    details = [{
        "exam": exam,
        "eligibility": eligibility.get(exam.pk),
        "registration": registration_by_exam.get(exam.pk),
        "is_eligible": bool(eligibility.get(exam.pk) and eligibility[exam.pk].is_eligible),
    } for exam in exams]
    payments = DiplomaExamPayment.objects.filter(
        registration__student=request.user
    ).select_related("registration", "registration__exam")
    return render(request, "admissions/diploma_exam_management.html", {
        "exam_details": details,
        "my_registrations": registrations,
        "my_payments": payments,
        "registration_form": DiplomaExamRegistrationForm(),
    })


@login_required(login_url="login")
@require_POST
def diploma_exam_register(request):
    form = DiplomaExamRegistrationForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Select a valid examination.")
        return redirect("diploma_exam_management")
    exam = form.cleaned_data["exam"]
    try:
        with transaction.atomic():
            exam = DiplomaExam.objects.select_for_update().get(pk=exam.pk)
            if not exam.registration_open:
                messages.error(request, "Registration is closed for this examination.")
                return redirect("diploma_exam_management")
            if not DiplomaExamEligibility.objects.filter(
                student=request.user, exam=exam, is_eligible=True
            ).exists():
                messages.error(request, "You are not eligible for this examination yet.")
                return redirect("diploma_exam_management")
            registration, created = DiplomaExamRegistration.objects.get_or_create(
                student=request.user, exam=exam,
                defaults={"fee_amount": exam.exam_fee},
            )
            if not created and registration.registration_status != "cancelled":
                messages.info(request, "You are already registered for this examination.")
                return redirect("diploma_exam_management")
            if not created:
                registration.registration_status = "registered"
                registration.fee_amount = exam.exam_fee
                registration.save(update_fields=["registration_status", "fee_amount"])
            DiplomaExamPayment.objects.get_or_create(
                registration=registration,
                status="pending",
                defaults={"amount": registration.fee_amount},
            )
    except IntegrityError:
        messages.error(request, "A registration already exists for this examination.")
        return redirect("diploma_exam_management")
    messages.success(request, "Registration created. The examination fee is pending.")
    return redirect("diploma_exam_management")

@login_required(login_url="login")
def eligibility_verification(request):

    if request.method == "POST":
        form = EligibilityVerificationForm(request.POST)

        if form.is_valid():
            student = form.cleaned_data["student"]
            exam = form.cleaned_data["exam"]

            try:
                with transaction.atomic():
                    record, created = (
                        DiplomaExamEligibility.objects
                        .select_for_update()
                        .get_or_create(
                            student=student,
                            exam=exam,
                            defaults={
                                "is_eligible": form.cleaned_data["is_eligible"],
                                "remarks": form.cleaned_data["remarks"],
                                "verified_by": request.user,
                                "verified_at": timezone.now(),
                            },
                        )
                    )

                    if not created:
                        record.is_eligible = form.cleaned_data["is_eligible"]
                        record.remarks = form.cleaned_data["remarks"]
                        record.verified_by = request.user
                        record.verified_at = timezone.now()

                        record.save(
                            update_fields=[
                                "is_eligible",
                                "remarks",
                                "verified_by",
                                "verified_at",
                            ]
                        )

                messages.success(
                    request,
                    "Student eligibility verification saved successfully.",
                )
                return redirect("eligibility_verification")

            except IntegrityError:
                messages.error(
                    request,
                    "The record could not be saved. Please refresh and try again.",
                )
        else:
            messages.error(
                request,
                "Please correct the errors in the form.",
            )
    else:
        form = EligibilityVerificationForm()

    records = (
        DiplomaExamEligibility.objects.select_related(
            "student",
            "exam",
            "verified_by",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "admissions/eligibility_verification.html",
        {
            "form": form,
            "records": records,
        },
    )


@login_required(login_url="login")
def exam_payment_verification(request, payment_id):
    # Only authorized examination staff may verify payments.
    if not (
        request.user.is_staff
        or request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "You do not have permission to verify examination payments."
        )

    payment = get_object_or_404(
        DiplomaExamPayment.objects.select_related(
            "registration",
            "registration__student",
            "registration__exam",
            "verified_by",
        ),
        pk=payment_id,
    )

    if request.method == "POST":
        with transaction.atomic():
            # Lock this payment while processing the submitted update.
            locked_payment = get_object_or_404(
                DiplomaExamPayment.objects.select_for_update(),
                pk=payment_id,
            )

            if locked_payment.status == "paid":
                messages.error(
                    request,
                    "This payment is already marked as paid. "
                    "Use your audited refund or reversal workflow "
                    "if a correction is required.",
                )
                return redirect(
                    "exam_payment_verification",
                    payment_id=locked_payment.pk,
                )

            form = PaymentVerificationForm(
                request.POST,
                instance=locked_payment,
            )

            if form.is_valid():
                new_status = form.cleaned_data["status"]

                # Confirm that the registration model supports the
                # payment status field before synchronizing it.
                try:
                    registration_status_field = (
                        DiplomaExamRegistration._meta.get_field(
                            "payment_status"
                        )
                    )
                except FieldDoesNotExist:
                    form.add_error(
                        None,
                        "The registration model does not have a "
                        "'payment_status' field. Add or map that field "
                        "before enabling status synchronization.",
                    )
                else:
                    allowed_registration_statuses = {
                        value
                        for value, label in (
                            registration_status_field.choices or []
                        )
                    }

                    if (
                        allowed_registration_statuses
                        and new_status not in allowed_registration_statuses
                    ):
                        form.add_error(
                            "status",
                            "This status is not supported by the "
                            "registration payment status field.",
                        )
                    else:
                        payment = form.save(commit=False)
                        payment.verified_by = request.user
                        payment.verified_at = timezone.now()
                        payment.save()

                        registration = (
                            DiplomaExamRegistration.objects
                            .select_for_update()
                            .get(pk=payment.registration_id)
                        )

                        registration.payment_status = new_status
                        registration.save(
                            update_fields=["payment_status"]
                        )

                        messages.success(
                            request,
                            "Payment verification saved successfully.",
                        )

                        return redirect(
                            "exam_payment_verification",
                            payment_id=payment.pk,
                        )

            # Keep the form errors visible on the same page.
            payment = get_object_or_404(
                DiplomaExamPayment.objects.select_related(
                    "registration",
                    "registration__student",
                    "registration__exam",
                    "verified_by",
                ),
                pk=payment_id,
            )

    else:
        form = PaymentVerificationForm(instance=payment)

    return render(
        request,
        "admissions/payment_verification.html",
        {
            "payment": payment,
            "form": form,
        },
    )

@login_required(login_url="login")
def hall_ticket_management(request):
    tickets = HallTicket.objects.select_related(
        "application", "application__student", "application__examination"
    ).order_by("-created_at")
    if request.method == "POST":
        application = get_object_or_404(ExamApplication, pk=request.POST.get("application_id"))
        if application.eligibility_status != "Eligible" or application.status != "Approved":
            messages.error(request, "Approve the application and verify eligibility before issuing a hall ticket.")
        else:
            try:
                payment = application.examapplicationpayment
            except ExamApplicationPayment.DoesNotExist:
                payment = None
            if not payment or payment.status != "Paid":
                messages.error(request, "A verified exam-fee payment is required before issuing the hall ticket.")
            else:
                ticket, created = HallTicket.objects.get_or_create(
                    application=application,
                    status="Active",
                    defaults={"issued_by": request.user},
                )
                messages.success(request, "Hall ticket issued." if created else f"Active ticket already exists: {ticket.hall_ticket_number}")
        return redirect("hall_ticket_management")
    return render(request, "admissions/hall_ticket_management.html", {
        "tickets": tickets,
        "applications": ExamApplication.objects.filter(
            status="Approved", eligibility_status="Eligible"
        ).select_related("student", "examination"),
    })


@login_required(login_url="login")
def result_verification(request):
    registration_number = request.GET.get("registration_number", "").strip()
    verified_result = None
    error_message = ""
    if registration_number:
        result = ExaminationResult.objects.filter(
            application__registration_number=registration_number,
            publication_status="Published",
        ).select_related(
            "application", "application__student", "application__examination",
            "application__examination__course"
        ).first()
        if result:
            verified_result = {
                "student_name": result.application.student.full_name,
                "registration_number": result.application.registration_number,
                "diploma_name": result.application.examination.course.name,
                "total_marks": result.total_marks_obtained,
                "percentage": result.percentage,
                "result_status": result.result_status,
                "grade": result.grade,
            }
        else:
            error_message = "No published result was found for that registration number."
    return render(request, "admissions/result_verification.html", {
        "registration_number": registration_number,
        "verified_result": verified_result,
        "error_message": error_message,
        "searched": bool(registration_number),
    })


@login_required(login_url="login")
def result_management(request):
    results = ExaminationResult.objects.select_related(
        "application", "application__student", "application__examination"
    ).order_by("-calculated_at")
    if request.method == "POST":
        result = get_object_or_404(ExaminationResult, pk=request.POST.get("result_id"))
        action = request.POST.get("action")
        if action == "calculate":
            result.calculate()
            messages.success(request, "Result recalculated from approved marks.")
        elif action == "publish":
            if not result.application.marks.filter(eval_status="Approved").exists():
                messages.error(request, "Approve marks before publishing the result.")
            else:
                result.publication_status = "Published"
                result.published_at = timezone.now()
                result.published_by = request.user
                result.save(update_fields=["publication_status", "published_at", "published_by", "calculated_at"])
                messages.success(request, "Result published.")
        return redirect("result_management")
    return render(request, "admissions/result_management.html", {"results": results})


@login_required(login_url="login")
def certificate_management(request):
    certificates = Certificate.objects.select_related("student", "course", "exam_result").all()
    return render(request, "admissions/certificate_management.html", {"certificates": certificates})



@login_required
def examination_mark_management(request):
    marks = ExaminationMark.objects.select_related(
        "application",
        "subject",
        "entered_by",
        "approved_by",
    ).all()

    status = request.GET.get("status", "").strip()

    valid_statuses = {
        choice[0] for choice in ExaminationMark.EVAL_STATUS_CHOICES
    }

    if status in valid_statuses:
        marks = marks.filter(eval_status=status)

    context = {
        "marks": marks,
        "total_marks": ExaminationMark.objects.count(),
        "draft_count": ExaminationMark.objects.filter(
            eval_status="Draft"
        ).count(),
        "submitted_count": ExaminationMark.objects.filter(
            eval_status="Submitted"
        ).count(),
        "approved_count": ExaminationMark.objects.filter(
            eval_status="Approved"
        ).count(),
        "selected_status": status,
    }

    return render(
        request,
        "admissions/examination_mark_management.html",
        context,
    )


@login_required
def examination_mark_create(request):
    if request.method == "POST":
        form = ExaminationMarkForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    mark = form.save(commit=False)
                    mark.entered_by = request.user
                    mark.eval_status = "Draft"
                    mark.full_clean()
                    mark.save()

                messages.success(
                    request,
                    "Examination marks saved successfully as Draft.",
                )
                return redirect("examination_mark_management")

            except IntegrityError:
                form.add_error(
                    None,
                    "Marks already exist for this application and subject.",
                )

            except Exception as exc:
                from django.core.exceptions import ValidationError

                if isinstance(exc, ValidationError):
                    form.add_error(None, exc)
                else:
                    raise
    else:
        form = ExaminationMarkForm()

    return render(
        request,
        "admissions/examination_mark_form.html",
        {
            "form": form,
            "page_title": "Enter Examination Marks",
            "button_text": "Save Marks",
        },
    )


@login_required
def examination_mark_edit(request, mark_id):
    mark = get_object_or_404(ExaminationMark, pk=mark_id)

    if mark.eval_status == "Approved":
        messages.error(
            request,
            "Approved marks cannot be edited.",
        )
        return redirect("examination_mark_management")

    if request.method == "POST":
        form = ExaminationMarkForm(request.POST, instance=mark)

        if form.is_valid():
            try:
                with transaction.atomic():
                    updated_mark = form.save(commit=False)
                    updated_mark.entered_by = mark.entered_by or request.user
                    updated_mark.eval_status = "Draft"
                    updated_mark.approved_by = None
                    updated_mark.full_clean()
                    updated_mark.save()

                messages.success(
                    request,
                    "Marks updated successfully as Draft.",
                )
                return redirect("examination_mark_management")

            except IntegrityError:
                form.add_error(
                    None,
                    "A mark record already exists for this subject and application.",
                )

            except Exception as exc:
                from django.core.exceptions import ValidationError

                if isinstance(exc, ValidationError):
                    form.add_error(None, exc)
                else:
                    raise
    else:
        form = ExaminationMarkForm(instance=mark)

    return render(
        request,
        "admissions/examination_mark_form.html",
        {
            "form": form,
            "page_title": "Edit Examination Marks",
            "button_text": "Update Marks",
            "mark": mark,
        },
    )


@login_required
@require_POST
def examination_mark_submit(request, mark_id):
    mark = get_object_or_404(ExaminationMark, pk=mark_id)

    if mark.eval_status != "Draft":
        messages.error(request, "Only Draft marks can be submitted.")
        return redirect("examination_mark_management")

    mark.full_clean()
    mark.eval_status = "Submitted"
    mark.save(update_fields=["eval_status", "updated_at"])

    messages.success(request, "Marks submitted for approval.")
    return redirect("examination_mark_management")


@login_required
@require_POST
def examination_mark_approve(request, mark_id):
    mark = get_object_or_404(ExaminationMark, pk=mark_id)

    # Replace this basic check with your application's
    # examiner/coordinator permission system.
    if not (
        request.user.is_superuser
        or request.user.is_staff
    ):
        messages.error(
            request,
            "You do not have permission to approve examination marks.",
        )
        return redirect("examination_mark_management")

    if mark.eval_status != "Submitted":
        messages.error(request, "Only Submitted marks can be approved.")
        return redirect("examination_mark_management")

    mark.full_clean()
    mark.eval_status = "Approved"
    mark.approved_by = request.user
    mark.save(update_fields=["eval_status", "approved_by", "updated_at"])

    messages.success(request, "Examination marks approved successfully.")
    return redirect("examination_mark_management")



@login_required
def exam_fee_payment_list(request):
    payments = ExamFeePayment.objects.select_related(
        "application",
        "entered_by",
        "verified_by",
    )

    status = request.GET.get("status", "").strip()
    valid_statuses = {
        value for value, label
        in ExamFeePayment.PAYMENT_STATUS_CHOICES
    }

    if status in valid_statuses:
        payments = payments.filter(status=status)

    context = {
        "payments": payments,
        "total_count": ExamFeePayment.objects.count(),
        "pending_count": ExamFeePayment.objects.filter(
            status="Pending"
        ).count(),
        "verified_count": ExamFeePayment.objects.filter(
            status="Verified"
        ).count(),
        "failed_count": ExamFeePayment.objects.filter(
            status="Failed"
        ).count(),
        "selected_status": status,
        "can_verify": request.user.is_staff or request.user.is_superuser,
    }

    return render(
        request,
        "admissions/exam_fee_payment_list.html",
        context,
    )


@login_required
def exam_fee_payment_create(request):
    if request.method == "POST":
        form = ExamFeePaymentForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    payment = form.save(commit=False)
                    payment.status = "Pending"
                    payment.entered_by = request.user
                    payment.verified_by = None
                    payment.verified_at = None
                    payment.full_clean()
                    payment.save()

                messages.success(
                    request,
                    "Exam fee payment record created successfully. "
                    "It is awaiting verification.",
                )
                return redirect("exam_fee_payment_list")

            except IntegrityError:
                form.add_error(
                    "transaction_id",
                    "This transaction ID is already in use.",
                )

    else:
        form = ExamFeePaymentForm()

    return render(
        request,
        "admissions/exam_fee_payment_form.html",
        {
            "form": form,
            "page_title": "Record Exam Fee Payment",
            "button_text": "Save Payment",
        },
    )


@login_required
@require_POST
def exam_fee_payment_verify(request, payment_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(
            request,
            "You do not have permission to verify payments.",
        )
        return redirect("exam_fee_payment_list")

    try:
        with transaction.atomic():
            payment = get_object_or_404(
                ExamFeePayment.objects.select_for_update(),
                pk=payment_id,
            )

            if payment.status != "Pending":
                messages.error(
                    request,
                    "Only pending payments can be verified.",
                )
                return redirect("exam_fee_payment_list")

            payment.status = "Verified"
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.full_clean()
            payment.save(
                update_fields=[
                    "status",
                    "verified_by",
                    "verified_at",
                    "updated_at",
                ]
            )

    except IntegrityError:
        messages.error(
            request,
            "Payment verification failed. Please check the payment record.",
        )
        return redirect("exam_fee_payment_list")

    messages.success(
        request,
        "Payment verified successfully.",
    )
    return redirect("exam_fee_payment_list")


@login_required
def subject_management(request):
    subjects = ExaminationSubject.objects.select_related(
        "examination",
        "examination__course",
        "examination__centre",
    )

    search_query = request.GET.get("q", "").strip()
    examination_id = request.GET.get("examination", "").strip()

    if search_query:
        subjects = subjects.filter(
            Q(subject_name__icontains=search_query)
            | Q(subject_code__icontains=search_query)
            | Q(examination__exam_name__icontains=search_query)
            | Q(examination__exam_code__icontains=search_query)
        )

    if examination_id.isdigit():
        subjects = subjects.filter(examination_id=int(examination_id))

    context = {
        "subjects": subjects,
        "examinations": Examination.objects.order_by("exam_name"),
        "total_subjects": ExaminationSubject.objects.count(),
        "total_examinations": Examination.objects.count(),
        "search_query": search_query,
        "selected_examination": examination_id,
    }

    return render(
        request,
        "admissions/subject_management.html",
        context,
    )


@login_required
def subject_create(request):
    if request.method == "POST":
        form = ExaminationSubjectForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()

                messages.success(
                    request,
                    "Subject added successfully.",
                )
                return redirect("subject_management")

            except IntegrityError:
                form.add_error(
                    "subject_code",
                    "This subject code already exists for this examination.",
                )
    else:
        form = ExaminationSubjectForm()

    return render(
        request,
        "admissions/subject_form.html",
        {
            "form": form,
            "page_title": "Add Examination Subject",
            "button_text": "Save Subject",
        },
    )


@login_required
def subject_edit(request, subject_id):
    subject = get_object_or_404(
        ExaminationSubject,
        pk=subject_id,
    )

    if request.method == "POST":
        form = ExaminationSubjectForm(
            request.POST,
            instance=subject,
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()

                messages.success(
                    request,
                    "Subject updated successfully.",
                )
                return redirect("subject_management")

            except IntegrityError:
                form.add_error(
                    "subject_code",
                    "This subject code already exists for this examination.",
                )
    else:
        form = ExaminationSubjectForm(instance=subject)

    return render(
        request,
        "admissions/subject_form.html",
        {
            "form": form,
            "page_title": "Edit Examination Subject",
            "button_text": "Update Subject",
            "subject": subject,
        },
    )


@login_required
@require_POST
def subject_delete(request, subject_id):
    subject = get_object_or_404(
        ExaminationSubject,
        pk=subject_id,
    )

    subject.delete()

    messages.success(
        request,
        "Subject deleted successfully.",
    )
    return redirect("subject_management")



@login_required
def exam_schedule_list(request):
    schedules = ExamSchedule.objects.select_related(
        "examination",
        "examination__course",
        "examination__centre",
    ).all()

    search_query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search_query:
        schedules = schedules.filter(
            Q(examination__exam_name__icontains=search_query)
            | Q(examination__exam_code__icontains=search_query)
            | Q(venue__icontains=search_query)
        )

    valid_statuses = dict(ExamSchedule.STATUS_CHOICES)

    if selected_status in valid_statuses:
        schedules = schedules.filter(status=selected_status)

    context = {
        "schedules": schedules,
        "search_query": search_query,
        "selected_status": selected_status,
        "total_schedules": ExamSchedule.objects.count(),
        "scheduled_count": ExamSchedule.objects.filter(
            status="SCHEDULED"
        ).count(),
        "completed_count": ExamSchedule.objects.filter(
            status="COMPLETED"
        ).count(),
        "cancelled_count": ExamSchedule.objects.filter(
            status="CANCELLED"
        ).count(),
        "status_choices": ExamSchedule.STATUS_CHOICES,
    }

    return render(
        request,
        "admissions/exam_schedule_list.html",
        context,
    )


@login_required
def exam_schedule_create(request):
    if request.method == "POST":
        form = ExamScheduleForm(request.POST)

        if form.is_valid():
            schedule = form.save(commit=False)

            try:
                schedule.full_clean()
                schedule.save()
                messages.success(
                    request,
                    "Examination schedule created successfully.",
                )
                return redirect("exam_schedule_list")

            except Exception as exc:
                from django.core.exceptions import ValidationError

                if isinstance(exc, ValidationError):
                    form.add_error(None, exc)
                else:
                    raise
    else:
        form = ExamScheduleForm()

    return render(
        request,
        "admissions/exam_schedule_form.html",
        {
            "form": form,
            "page_title": "Add Exam Schedule",
            "button_text": "Save Schedule",
        },
    )


@login_required
def exam_schedule_edit(request, schedule_id):
    schedule = get_object_or_404(
        ExamSchedule,
        pk=schedule_id,
    )

    if request.method == "POST":
        form = ExamScheduleForm(
            request.POST,
            instance=schedule,
        )

        if form.is_valid():
            try:
                updated_schedule = form.save(commit=False)
                updated_schedule.full_clean()
                updated_schedule.save()

                messages.success(
                    request,
                    "Examination schedule updated successfully.",
                )
                return redirect("exam_schedule_list")

            except Exception as exc:
                from django.core.exceptions import ValidationError

                if isinstance(exc, ValidationError):
                    form.add_error(None, exc)
                else:
                    raise
    else:
        form = ExamScheduleForm(instance=schedule)

    return render(
        request,
        "admissions/exam_schedule_form.html",
        {
            "form": form,
            "schedule": schedule,
            "page_title": "Edit Exam Schedule",
            "button_text": "Update Schedule",
        },
    )


@login_required
@require_POST
def exam_schedule_delete(request, schedule_id):
    schedule = get_object_or_404(
        ExamSchedule,
        pk=schedule_id,
    )

    schedule.delete()

    messages.success(
        request,
        "Examination schedule deleted successfully.",
    )

    return redirect("exam_schedule_list")


@login_required
def exam_centres_list(request):
    centres = ExamCentre.objects.all()

    search_query = request.GET.get("q", "").strip()
    selected_mode = request.GET.get("mode", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search_query:
        centres = centres.filter(
            Q(centre_name__icontains=search_query)
            | Q(centre_code__icontains=search_query)
            | Q(city__icontains=search_query)
            | Q(contact_person__icontains=search_query)
        )

    if selected_mode in dict(ExamCentre.MODE_CHOICES):
        centres = centres.filter(exam_mode=selected_mode)

    if selected_status in dict(ExamCentre.STATUS_CHOICES):
        centres = centres.filter(status=selected_status)

    context = {
        "centres": centres,
        "search_query": search_query,
        "selected_mode": selected_mode,
        "selected_status": selected_status,
        "total_centres": ExamCentre.objects.count(),
        "active_centres": ExamCentre.objects.filter(
            status="ACTIVE"
        ).count(),
        "inactive_centres": ExamCentre.objects.filter(
            status="INACTIVE"
        ).count(),
        "total_capacity": sum(
            ExamCentre.objects.values_list("capacity", flat=True)
        ),
    }

    return render(
        request,
        "admissions/exam_centres_list.html",
        context,
    )


@login_required
def exam_centre_create(request):
    if request.method == "POST":
        form = ExamCentreForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Exam centre added successfully.",
            )
            return redirect("exam_centres_list")
    else:
        form = ExamCentreForm()

    return render(
        request,
        "admissions/exam_centre_form.html",
        {
            "form": form,
            "page_title": "Add Exam Centre",
            "button_text": "Save Centre",
        },
    )


@login_required
def exam_centre_edit(request, centre_id):
    centre = get_object_or_404(ExamCentre, pk=centre_id)

    if request.method == "POST":
        form = ExamCentreForm(request.POST, instance=centre)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Exam centre updated successfully.",
            )
            return redirect("exam_centres_list")
    else:
        form = ExamCentreForm(instance=centre)

    return render(
        request,
        "admissions/exam_centre_form.html",
        {
            "form": form,
            "page_title": "Edit Exam Centre",
            "button_text": "Update Centre",
        },
    )


@login_required
def exam_centre_delete(request, centre_id):
    centre = get_object_or_404(ExamCentre, pk=centre_id)

    if request.method == "POST":
        try:
            centre.delete()
            messages.success(
                request,
                "Exam centre deleted successfully.",
            )
        except Exception:
            messages.error(
                request,
                "This centre cannot be deleted because it may be "
                "linked to an existing examination. Deactivate it instead."
            )

    return redirect("exam_centres_list")

@login_required
def hall_ticket_management(request):
    tickets = HallTicket.objects.all()

    search = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search:
        from django.db.models import Q

        tickets = tickets.filter(
            Q(hall_ticket_number__icontains=search)
            | Q(student_name__icontains=search)
            | Q(student_id__icontains=search)
            | Q(exam_name__icontains=search)
            | Q(centre_name__icontains=search)
        )

    if selected_status in {"GENERATED", "REVOKED"}:
        tickets = tickets.filter(status=selected_status)

    context = {
        "tickets": tickets,
        "search": search,
        "selected_status": selected_status,
        "total_tickets": HallTicket.objects.count(),
        "active_tickets": HallTicket.objects.filter(
            status="GENERATED"
        ).count(),
        "revoked_tickets": HallTicket.objects.filter(
            status="REVOKED"
        ).count(),
    }

    return render(
        request,
        "admissions/hall_ticket_management.html",
        context,
    )


@login_required
def hall_ticket_create(request):
    if request.method == "POST":
        form = HallTicketForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    ticket = form.save(commit=False)

                    # Generate a ticket number if the user left it blank.
                    if not ticket.hall_ticket_number:
                        ticket.hall_ticket_number = (
                            f"HT-{timezone.now():%Y%m%d}-"
                            f"{uuid4().hex[:8].upper()}"
                        )

                    # New tickets start as generated.
                    ticket.status = "GENERATED"
                    ticket.save()

                messages.success(
                    request,
                    f"Hall ticket {ticket.hall_ticket_number} created successfully.",
                )
                return redirect("hall_ticket_management")

            except IntegrityError:
                form.add_error(
                    "hall_ticket_number",
                    "This hall ticket number or exam application is already in use.",
                )
    else:
        form = HallTicketForm(initial={"status": "GENERATED"})

    return render(
        request,
        "admissions/hall_ticket_form.html",
        {"form": form},
    )


@login_required
def hall_ticket_download(request, ticket_id):
    ticket = get_object_or_404(HallTicket, pk=ticket_id)

    if ticket.status != "GENERATED":
        messages.error(request, "This hall ticket is revoked and cannot be downloaded.")
        return redirect("hall_ticket_management")

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    elements = [
        Paragraph("EduMate - Examination Hall Ticket", styles["Title"]),
        Spacer(1, 8 * mm),
        Paragraph(
            f"<b>Hall Ticket Number:</b> {ticket.hall_ticket_number or 'Not assigned'}",
            styles["Normal"],
        ),
        Spacer(1, 4 * mm),
    ]

    rows = [
        ["Student Name", ticket.student_name or "—"],
        ["Student ID", ticket.student_id or "—"],
        ["Examination", ticket.exam_name or "—"],
        [
            "Exam Date",
            ticket.exam_date.strftime("%d %B %Y") if ticket.exam_date else "—",
        ],
        [
            "Start Time",
            ticket.start_time.strftime("%I:%M %p") if ticket.start_time else "—",
        ],
        [
            "End Time",
            ticket.end_time.strftime("%I:%M %p") if ticket.end_time else "—",
        ],
        ["Examination Centre", ticket.centre_name or "—"],
        ["Venue", ticket.venue or "—"],
        ["Seat Number", ticket.seat_number or "—"],
        ["Status", ticket.get_status_display()],
    ]

    table = Table(rows, colWidths=[50 * mm, 110 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2ff")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#172033")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7deea")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 8 * mm))
    elements.append(
        Paragraph(
            "Please arrive at the examination centre before the scheduled start time.",
            styles["Normal"],
        )
    )

    document.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{ticket.hall_ticket_number or "hall-ticket"}.pdf"'
    )
    return response


@login_required
@require_POST
def hall_ticket_revoke(request, ticket_id):
    ticket = get_object_or_404(HallTicket, pk=ticket_id)

    if ticket.status == "GENERATED":
        ticket.status = "REVOKED"
        ticket.save(update_fields=["status"])
        messages.success(request, "Hall ticket revoked successfully.")
    else:
        messages.info(request, "This hall ticket is already revoked.")

    return redirect("hall_ticket_management")



@login_required
def examination_results(request):
    form = ExaminationResultFilterForm(request.GET or None)

    results = ExaminationResult.objects.select_related(
        "application"
    ).all()

    if form.is_valid():
        registration_number = form.cleaned_data.get("registration_number")
        result_status = form.cleaned_data.get("result_status")
        publication_status = form.cleaned_data.get("publication_status")

        if registration_number:
            results = results.filter(
                application__registration_number__icontains=registration_number
            )

        if result_status:
            results = results.filter(result_status=result_status)

        if publication_status:
            results = results.filter(
                publication_status=publication_status
            )

    context = {
        "form": form,
        "results": results,
        "total_results": ExaminationResult.objects.count(),
        "published_results": ExaminationResult.objects.filter(
            publication_status="Published"
        ).count(),
        "pending_results": ExaminationResult.objects.filter(
            publication_status__in=["Draft", "Approved"]
        ).count(),
        "passed_results": ExaminationResult.objects.filter(
            result_status="Pass"
        ).count(),
    }

    return render(
        request,
        "admissions/examination_results.html",
        context,
    )


@login_required
@require_POST
def examination_result_calculate(request, application_id):
    application = get_object_or_404(
        ExamApplication,
        pk=application_id,
    )

    marks = ExaminationMark.objects.filter(
        application=application
    )

    if not marks.exists():
        messages.error(
            request,
            "Cannot calculate the result because no examination marks exist.",
        )
        return redirect("examination_results")

    if marks.exclude(eval_status="Approved").exists():
        messages.error(
            request,
            "All examination marks must be approved before calculating the result.",
        )
        return redirect("examination_results")

    result, created = ExaminationResult.objects.get_or_create(
        application=application,
    )

    if result.publication_status == "Published":
        messages.error(
            request,
            "A published result cannot be recalculated.",
        )
        return redirect("examination_results")

    result.calculate()

    if result.total_max_marks <= 0:
        messages.error(
            request,
            "The result could not be calculated. Please check the subject maximum marks.",
        )
        return redirect("examination_results")

    messages.success(
        request,
        f"Result calculated successfully for {application.registration_number}.",
    )

    return redirect("examination_results")


@login_required
@require_POST
def examination_result_publish(request, result_id):
    result = get_object_or_404(
        ExaminationResult,
        pk=result_id,
    )

    if result.publication_status == "Published":
        messages.info(request, "This result is already published.")
        return redirect("examination_results")

    marks = ExaminationMark.objects.filter(
        application=result.application
    )

    if not marks.exists() or marks.exclude(eval_status="Approved").exists():
        messages.error(
            request,
            "Approve all examination marks before publishing the result.",
        )
        return redirect("examination_results")

    if result.total_max_marks <= 0:
        messages.error(
            request,
            "Calculate the result before publishing it.",
        )
        return redirect("examination_results")

    result.publication_status = "Published"
    result.published_at = timezone.now()
    result.published_by = request.user
    result.save(
        update_fields=[
            "publication_status",
            "published_at",
            "published_by",
        ]
    )

    messages.success(request, "Examination result published successfully.")
    return redirect("examination_results")


@login_required
def student_delete_confirm(request, pk):

    student = get_object_or_404(Student, pk=pk)

    return render(
        request,
        'admissions/student_delete.html',
        {
            'student': student
        }
    )


@login_required
@require_POST
def student_delete(request, pk):

    student = get_object_or_404(Student, pk=pk)

    student_name = student.full_name

    # Change student status to inactive
    student.is_active = False
    student.save(update_fields=['is_active'])

    messages.success(
        request,
        f"Student {student_name} has been deactivated successfully."
    )

    return redirect('student_list')