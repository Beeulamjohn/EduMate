
from decimal import Decimal
import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import HallTicket
from .models import (
    CourseCategory,
    Course,
    Batch,
    Enquiry,
    Student,
    Admission,
    AdmissionDocument,
)
from .models import CounsellingRecord
from .models import AdmissionSettings
from .models import FeeStructure, FeeInstallment, FeePayment, Invoice
from django.db.models import Sum
from .models import ExamFeePayment
from .models import FeeReminder
from django.contrib.auth import get_user_model

from .models import (
    DiplomaExam, DiplomaExamEligibility, DiplomaExamPayment,
    Examination, ExaminationCentre, ExaminationSubject,
)
from .models import ExamCentre
from .models import (
    ExaminationMark,
    ExamApplication,
    ExaminationSubject,
)
from .models import ExamSchedule

User = get_user_model()

class StyledModelForm(forms.ModelForm):
    """Apply consistent Bootstrap styling to model form fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = [
            "student_name",
            "mobile",
            "email",
            "location",
            "qualification",
            "college",
            "course_interested",
            "course_type",
            "lead_source",
            "assigned_counsellor",
            "enquiry_date",
            "followup_date",
            "remarks",
            "status",
        ]

        labels = {
            "student_name": "Student Name",
            "mobile": "Mobile Number",
            "email": "Email Address",
            "location": "Location",
            "qualification": "Qualification",
            "college": "College",
            "course_interested": "Course Interested",
            "course_type": "Course Type",
            "lead_source": "Lead Source",
            "assigned_counsellor": "Counsellor",
            "enquiry_date": "Enquiry Date",
            "followup_date": "Follow-up Date",
            "remarks": "Remarks",
            "status": "Enquiry Status",
        }

        widgets = {
            "student_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter student's full name",
            }),
            "mobile": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter mobile number",
                "inputmode": "tel",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter email address",
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter location",
            }),
            "qualification": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter qualification",
            }),
            "college": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter college name",
            }),
            "course_interested": forms.Select(attrs={
                "class": "form-control",
            }),
            "course_type": forms.Select(attrs={
                "class": "form-control",
            }),
            "lead_source": forms.Select(attrs={
                "class": "form-control",
            }),
            "assigned_counsellor": forms.Select(attrs={
                "class": "form-control",
            }),
            "enquiry_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "followup_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter enquiry notes or remarks",
                "rows": 3,
            }),
            "status": forms.Select(attrs={
                "class": "form-control",
            }),
        }

class CounsellingRecordForm(forms.ModelForm):
    class Meta:
        model = CounsellingRecord

        fields = [
            "enquiry",
            "counsellor",
            "student_requirements",
            "career_objective",
            "recommended_course",
            "fee_discussion",
            "scholarship_details",
            "counselling_status",
            "next_followup_date",
            "remarks",
        ]

        labels = {
            "enquiry": "Student Enquiry",
            "counsellor": "Assigned Counsellor",
            "student_requirements": "Student Requirements",
            "career_objective": "Career Objective",
            "recommended_course": "Recommended Course",
            "fee_discussion": "Fee Discussion",
            "scholarship_details": "Scholarship / Discount",
            "counselling_status": "Counselling Status",
            "next_followup_date": "Next Follow-up Date",
            "remarks": "Remarks",
        }

        widgets = {
            "enquiry": forms.Select(attrs={
                "class": "form-control",
            }),
            "counsellor": forms.Select(attrs={
                "class": "form-control",
            }),
            "student_requirements": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter student requirements",
                "rows": 3,
            }),
            "career_objective": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter the student's career objective",
                "rows": 3,
            }),
            "recommended_course": forms.Select(attrs={
                "class": "form-control",
            }),
            "fee_discussion": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter fee discussion details",
                "rows": 3,
            }),
            "scholarship_details": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter scholarship or discount details",
            }),
            "counselling_status": forms.Select(attrs={
                "class": "form-control",
            }),
            "next_followup_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter counselling remarks",
                "rows": 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optional fields should not be required by the form.
        for field_name in [
            "counsellor",
            "student_requirements",
            "career_objective",
            "recommended_course",
            "fee_discussion",
            "scholarship_details",
            "next_followup_date",
            "remarks",
        ]:
            self.fields[field_name].required = False

        self.fields["enquiry"].queryset = (
            self.fields["enquiry"].queryset.order_by("-enquiry_date")
        )

        self.fields["counsellor"].queryset = (
            self.fields["counsellor"].queryset.order_by("username")
        )

        self.fields["recommended_course"].queryset = (
            self.fields["recommended_course"].queryset.order_by("name")
        )


class CourseForm(StyledModelForm):
    class Meta:
        model = Course
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        fee = cleaned_data.get("fee")

        if fee is not None and fee < Decimal("0.00"):
            self.add_error("fee", "Course fee cannot be negative.")

        return cleaned_data


class BatchForm(StyledModelForm):
    class Meta:
        model = Batch
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "Batch end date cannot be before the start date.",
            )

        return cleaned_data


class AdmissionRegistrationForm(forms.Form):
    """
    Collect student, admission, and document details.

    The view must save the Student, Admission, and uploaded
    AdmissionDocument objects separately.
    """

    enquiry_id = forms.ModelChoiceField(
        queryset=Enquiry.objects.all(),
        required=False,
        empty_label="Select enquiry",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    mobile = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    dob = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    gender = forms.ChoiceField(
        choices=Student.GENDER_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "class": "form-control"}
        ),
    )

    location = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    highest_qualification = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    university = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    college = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    passing_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    percentage_cgpa = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
            }
        ),
    )

    photo = forms.ImageField(required=False)

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    batch = forms.ModelChoiceField(
        queryset=Batch.objects.none(),
        required=False,
        empty_label="Select batch",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    delivery_mode = forms.ChoiceField(
        choices=Admission.DELIVERY_MODE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    admission_date = forms.DateField(
        required=False,
        initial=timezone.localdate,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    course_fee = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "readonly": "readonly",
            }
        ),
    )

    scholarship_discount = forms.DecimalField(
        required=False,
        initial=Decimal("0.00"),
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
            }
        ),
    )

    amount_paid = forms.DecimalField(
        required=False,
        initial=Decimal("0.00"),
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
            }
        ),
    )

    doc_id_proof = forms.FileField(required=False)
    doc_education = forms.FileField(required=False)
    doc_resume = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["batch"].queryset = Batch.objects.filter(
            status__in=["Upcoming", "Ongoing"]
        )

        if self.is_bound:
            course_id = self.data.get("course")

            if course_id:
                self.fields["batch"].queryset = (
                    Batch.objects.filter(
                        course_id=course_id,
                        status__in=["Upcoming", "Ongoing"],
                    )
                )

    def clean_mobile(self):
        mobile = self.cleaned_data.get("mobile", "")
        digits = re.sub(r"\D", "", mobile)

        if not 10 <= len(digits) <= 15:
            raise ValidationError(
                "Enter a valid mobile number containing 10 to 15 digits."
            )

        return mobile

    def clean(self):
        cleaned_data = super().clean()

        course = cleaned_data.get("course")
        batch = cleaned_data.get("batch")
        course_fee = cleaned_data.get("course_fee")
        discount = cleaned_data.get("scholarship_discount") or Decimal("0.00")
        amount_paid = cleaned_data.get("amount_paid") or Decimal("0.00")
        dob = cleaned_data.get("dob")
        passing_year = cleaned_data.get("passing_year")
        percentage_cgpa = cleaned_data.get("percentage_cgpa")

        if dob and dob > timezone.localdate():
            self.add_error("dob", "Date of birth cannot be in the future.")

        if passing_year and not 1950 <= passing_year <= timezone.localdate().year:
            self.add_error(
                "passing_year",
                "Enter a valid passing year.",
            )

        if percentage_cgpa is not None and percentage_cgpa < 0:
            self.add_error(
                "percentage_cgpa",
                "Percentage/CGPA cannot be negative.",
            )

        if course:
            # Always use the course fee stored in the database.
            course_fee = course.fee
            cleaned_data["course_fee"] = course_fee

        if batch and course and batch.course_id != course.pk:
            self.add_error(
                "batch",
                "The selected batch does not belong to the selected course.",
            )

        if course_fee is not None:
            if discount > course_fee:
                self.add_error(
                    "scholarship_discount",
                    "Discount cannot exceed the course fee.",
                )
            else:
                payable = course_fee - discount

                if amount_paid > payable:
                    self.add_error(
                        "amount_paid",
                        "Amount paid cannot exceed the final payable amount.",
                    )

        return cleaned_data


class DocumentVerificationForm(StyledModelForm):
    class Meta:
        model = AdmissionDocument
        fields = [
            "verification_status",
            "verification_remarks",
        ]
        widgets = {
            "verification_remarks": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
        }


class PaymentRecordForm(forms.Form):
    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
            }
        ),
    )

    payment_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    payment_method = forms.ChoiceField(
        choices=[
            ("Cash", "Cash"),
            ("UPI", "UPI"),
            ("Bank Transfer", "Bank Transfer"),
            ("Card", "Card"),
            ("Cheque", "Cheque"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    transaction_reference = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "class": "form-control"}
        ),
    )


# Backward-compatible form name for views importing CounsellingForm.
CounsellingForm = CounsellingRecordForm



class AdmissionReportFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="Search student",
        widget=forms.TextInput(attrs={
            "placeholder": "Student name or admission number",
            "class": "report-input",
        }),
    )

    status = forms.ChoiceField(
        required=False,
        label="Admission status",
        choices=[
            ("", "All statuses"),
            ("Pending", "Pending"),
            ("Confirmed", "Confirmed"),
        ],
        widget=forms.Select(attrs={
            "class": "report-select",
        }),
    )


class AdmissionSettingsForm(forms.ModelForm):
    class Meta:
        model = AdmissionSettings

        fields = [
            "institution_name",
            "contact_email",
            "contact_phone",
            "admission_number_prefix",
            "default_admission_status",
            "require_document_verification",
        ]

        widgets = {
            "institution_name": forms.TextInput(attrs={
                "class": "settings-input",
                "placeholder": "Enter institution name",
            }),

            "contact_email": forms.EmailInput(attrs={
                "class": "settings-input",
                "placeholder": "admin@example.com",
            }),

            "contact_phone": forms.TextInput(attrs={
                "class": "settings-input",
                "placeholder": "Enter contact number",
            }),

            "admission_number_prefix": forms.TextInput(attrs={
                "class": "settings-input",
                "placeholder": "SC-ADM",
            }),

            "default_admission_status": forms.Select(attrs={
                "class": "settings-input",
            }),

            "require_document_verification": forms.CheckboxInput(
                attrs={"class": "settings-checkbox"}
            ),
        }

    def clean_admission_number_prefix(self):
        prefix = self.cleaned_data["admission_number_prefix"].strip()

        if not prefix:
            raise forms.ValidationError(
                "Admission number prefix is required."
            )

        if any(char.isspace() for char in prefix):
            raise forms.ValidationError(
                "Admission number prefix cannot contain spaces."
            )

        return prefix





class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = [
            "course",
            "course_fee",
            "registration_fee",
            "admission_fee",
            "material_fee",
            "exam_fee",
            "project_fee",
            "certification_fee",
            "other_fee",
            "discount",
            "tax_percentage",
        ]
        widgets = {
            "course": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter course name",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        subtotal = sum(
            (
                cleaned_data.get(field) or Decimal("0.00")
                for field in [
                    "course_fee",
                    "registration_fee",
                    "admission_fee",
                    "material_fee",
                    "exam_fee",
                    "project_fee",
                    "certification_fee",
                    "other_fee",
                ]
            ),
            Decimal("0.00"),
        )
        discount = cleaned_data.get("discount") or Decimal("0.00")

        if discount > subtotal:
            self.add_error("discount", "Discount cannot exceed the total fees.")

        return cleaned_data


class FeeInstallmentForm(forms.ModelForm):
    class Meta:
        model = FeeInstallment
        fields = [
            "student",
            "course",
            "batch",
            "counsellor",
            "installment_number",
            "amount",
            "amount_paid",
            "due_date",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        amount_paid = cleaned_data.get("amount_paid") or Decimal("0.00")

        if amount is not None and amount_paid > amount:
            self.add_error(
                "amount_paid",
                "Paid amount cannot exceed the installment amount.",
            )

        return cleaned_data


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = [
            "installment",
            "student",
            "course",
            "amount",
            "payment_date",
            "payment_mode",
            "transaction_id",
            "remarks",
        ]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "remarks": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        installment = cleaned_data.get("installment")
        amount = cleaned_data.get("amount")

        if installment and amount is not None:
            existing_paid = (
                installment.payments
                .filter(status="active")
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            # Exclude this payment if editing an existing record.
            if self.instance and self.instance.pk:
                previous_amount = self.instance.amount
                if self.instance.status == "active":
                    existing_paid -= previous_amount

            available = installment.amount - existing_paid

            if amount > available:
                self.add_error(
                    "amount",
                    f"Payment exceeds the remaining installment balance "
                    f"of ₹{max(Decimal('0.00'), available):.2f}.",
                )

        return cleaned_data


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "student",
            "invoice_date",
            "total_amount",
            "paid_amount",
            "pdf_file",
        ]
        widgets = {
            "invoice_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("total_amount")
        paid = cleaned_data.get("paid_amount") or Decimal("0.00")

        if total is not None and paid > total:
            self.add_error(
                "paid_amount",
                "Paid amount cannot exceed the invoice total.",
            )

        return cleaned_data


class OutstandingFeesFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="Search student",
        max_length=100,
        widget=forms.TextInput(attrs={
            "placeholder": "Student name, ID or admission number",
            "class": "outstanding-search-input",
        }),
    )

    minimum_balance = forms.DecimalField(
        required=False,
        min_value=0,
        label="Minimum balance",
        widget=forms.NumberInput(attrs={
            "placeholder": "Minimum amount",
            "class": "outstanding-filter-input",
            "step": "0.01",
        }),
    )


class FeeReminderForm(forms.ModelForm):

    class Meta:
        model = FeeReminder
        fields = [
            "admission",
            "reminder_date",
            "due_date",
            "message",
            "status",
        ]

        widgets = {
            "admission": forms.Select(attrs={
                "class": "reminder-input",
            }),
            "reminder_date": forms.DateInput(attrs={
                "class": "reminder-input",
                "type": "date",
            }),
            "due_date": forms.DateInput(attrs={
                "class": "reminder-input",
                "type": "date",
            }),
            "message": forms.Textarea(attrs={
                "class": "reminder-input reminder-textarea",
                "rows": 4,
                "placeholder": (
                    "Enter the outstanding fee reminder message..."
                ),
            }),
            "status": forms.Select(attrs={
                "class": "reminder-input",
            }),
        }

        labels = {
            "admission": "Student Admission",
            "reminder_date": "Reminder Date",
            "due_date": "Fee Due Date",
            "message": "Reminder Message",
            "status": "Reminder Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["admission"].queryset = (
            Admission.objects
            .filter(outstanding_balance__gt=0)
            .select_related("student", "course")
            .order_by("student__full_name")
        )

        self.fields["admission"].empty_label = (
            "Select a student with outstanding fees"
        )

    def clean(self):
        cleaned_data = super().clean()

        reminder_date = cleaned_data.get("reminder_date")
        due_date = cleaned_data.get("due_date")
        admission = cleaned_data.get("admission")

        if reminder_date and due_date and due_date < reminder_date:
            self.add_error(
                "due_date",
                "The due date cannot be earlier than the reminder date.",
            )

        if admission and admission.outstanding_balance <= 0:
            self.add_error(
                "admission",
                "This admission has no outstanding fee balance.",
            )

        return cleaned_data


class FeeReminderFilterForm(forms.Form):

    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "reminder-input",
            "placeholder": "Search student or admission number",
        }),
    )

    status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All statuses"),
            *FeeReminder.STATUS_CHOICES,
        ],
        widget=forms.Select(attrs={
            "class": "reminder-input",
        }),
    )


class DiplomaExamRegistrationForm(forms.Form):
    exam = forms.ModelChoiceField(
        queryset=DiplomaExam.objects.none(),
        empty_label="Choose an examination",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exam"].queryset = DiplomaExam.objects.filter(
            is_active=True, registration_deadline__gte=timezone.now()
        ).order_by("exam_date")
class EligibilityVerificationForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Student",
        empty_label="Select a student",
        widget=forms.Select(
            attrs={"class": "form-control"}
        ),
    )

    exam = forms.ModelChoiceField(
        queryset=DiplomaExam.objects.none(),
        label="Diploma Examination",
        empty_label="Select an examination",
        widget=forms.Select(
            attrs={"class": "form-control"}
        ),
    )

    is_eligible = forms.ChoiceField(
        label="Eligibility Decision",
        choices=[
            ("", "Select decision"),
            ("yes", "Eligible"),
            ("no", "Not Eligible"),
        ],
        widget=forms.Select(
            attrs={"class": "form-control"}
        ),
    )

    remarks = forms.CharField(
        label="Remarks",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter verification remarks...",
            }
        ),
    )

    class Meta:
        model = DiplomaExamEligibility
        fields = ["student", "exam", "is_eligible", "remarks"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["student"].queryset = (
            User.objects.filter(is_active=True).order_by("username")
        )

        self.fields["exam"].queryset = (
            DiplomaExam.objects.filter(is_active=True).order_by("exam_date")
        )

        if self.instance and self.instance.pk:
            self.fields["is_eligible"].initial = (
                "yes" if self.instance.is_eligible else "no"
            )

    def clean_is_eligible(self):
        value = self.cleaned_data["is_eligible"]
        return value == "yes"
    
class PaymentVerificationForm(forms.ModelForm):
    class Meta:
        model = DiplomaExamPayment
        fields = [
            "status",
            "transaction_reference",
            "verification_notes",
        ]

        labels = {
            "status": "Payment Status",
            "transaction_reference": "Transaction Reference",
            "verification_notes": "Verification Notes",
        }

        widgets = {
            "status": forms.Select(
                attrs={"class": "form-control"},
            ),
            "transaction_reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter transaction reference",
                },
            ),
            "verification_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter verification notes",
                },
            ),
        }

    def clean_status(self):
        status = self.cleaned_data["status"]

        allowed_statuses = {
            value
            for value, label in DiplomaExamPayment.PAYMENT_STATUS_CHOICES
        }

        if status not in allowed_statuses:
            raise forms.ValidationError(
                "Please select a valid payment status."
            )

        return status

class BaseEduMateModelForm(forms.ModelForm):
    """Apply consistent form styling to the examination management forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()


class ExaminationForm(BaseEduMateModelForm):
    class Meta:
        model = Examination
        fields = [
            "exam_code",
            "exam_name",
            "course",
            "centre",
            "exam_date",
            "exam_mode",
            "status",
        ]

        widgets = {
            "exam_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter examination code",
            }),
            "exam_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter examination name",
            }),
            "course": forms.Select(attrs={
                "class": "form-control",
            }),
            "centre": forms.Select(attrs={
                "class": "form-control",
            }),
            "exam_date": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
            "exam_mode": forms.Select(attrs={
                "class": "form-control",
            }),
            "status": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def clean_exam_date(self):
        exam_date = self.cleaned_data.get("exam_date")
        return exam_date


class ExaminationCentreForm(BaseEduMateModelForm):
    class Meta:
        model = ExaminationCentre
        fields = ["name", "city", "capacity", "is_active"]


class ExaminationSubjectForm(BaseEduMateModelForm):
    class Meta:
        model = ExaminationSubject
        fields = [
            "examination",
            "subject_name",
            "subject_code",
            "max_marks",
        ]

        widgets = {
            "examination": forms.Select(attrs={
                "class": "form-control",
            }),
            "subject_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter subject name",
            }),
            "subject_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: PY101",
            }),
            "max_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "step": "1",
                "placeholder": "Enter maximum marks",
            }),
        }

    def clean_subject_code(self):
        return self.cleaned_data["subject_code"].strip().upper()

    def clean(self):
        cleaned_data = super().clean()
        examination = cleaned_data.get("examination")
        subject_code = cleaned_data.get("subject_code")

        if examination and subject_code:
            existing = ExaminationSubject.objects.filter(
                examination=examination,
                subject_code=subject_code,
            )

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                self.add_error(
                    "subject_code",
                    "This subject code already exists for this examination.",
                )

        return cleaned_data



class ExaminationMarkForm(forms.ModelForm):
    class Meta:
        model = ExaminationMark
        fields = [
            "application",
            "subject",
            "marks_obtained",
            "internal_marks",
            "practical_marks",
            "is_absent",
            "examiner_remarks",
        ]

        widgets = {
            "application": forms.Select(
                attrs={"class": "form-control"}
            ),
            "subject": forms.Select(
                attrs={"class": "form-control"}
            ),
            "marks_obtained": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
            "internal_marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
            "practical_marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
            "is_absent": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "examiner_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter examiner remarks (optional)",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        is_absent = cleaned_data.get("is_absent")
        application = cleaned_data.get("application")
        subject = cleaned_data.get("subject")

        if application and subject:
            # An application can have only one mark record per subject.
            duplicate = ExaminationMark.objects.filter(
                application=application,
                subject=subject,
            )

            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)

            if duplicate.exists():
                raise ValidationError(
                    "Marks already exist for this application and subject."
                )

        if is_absent:
            cleaned_data["marks_obtained"] = 0
            cleaned_data["internal_marks"] = 0
            cleaned_data["practical_marks"] = 0

        return cleaned_data


class ExamFeePaymentForm(forms.ModelForm):
    class Meta:
        model = ExamFeePayment
        fields = [
            "application",
            "fee_amount",
            "amount_paid",
            "payment_method",
            "transaction_id",
            "payment_date",
            "remarks",
        ]

        widgets = {
            "application": forms.Select(
                attrs={"class": "form-control"}
            ),
            "fee_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "amount_paid": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
            "payment_method": forms.Select(
                attrs={"class": "form-control"}
            ),
            "transaction_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter transaction/reference ID",
                }
            ),
            "payment_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional payment remarks",
                }
            ),
        }

    def clean_transaction_id(self):
        transaction_id = self.cleaned_data.get("transaction_id")
        return transaction_id.strip() if transaction_id else None

    def clean(self):
        cleaned_data = super().clean()

        fee_amount = cleaned_data.get("fee_amount")
        amount_paid = cleaned_data.get("amount_paid")

        if (
            fee_amount is not None
            and amount_paid is not None
            and amount_paid > fee_amount
        ):
            self.add_error(
                "amount_paid",
                "Amount paid cannot exceed the examination fee.",
            )

        return cleaned_data



class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule

        fields = [
            "examination",
            "schedule_date",
            "start_time",
            "end_time",
            "venue",
            "status",
            "instructions",
        ]

        widgets = {
            "examination": forms.Select(attrs={
                "class": "form-control",
            }),

            "schedule_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),

            "start_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),

            "end_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),

            "venue": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter examination venue",
            }),

            "status": forms.Select(attrs={
                "class": "form-control",
            }),

            "instructions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter optional examination instructions",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            self.add_error(
                "end_time",
                "End time must be later than start time.",
            )

        return cleaned_data


class ExamCentreForm(forms.ModelForm):
    class Meta:
        model = ExamCentre
        fields = [
            "centre_code",
            "centre_name",
            "address",
            "city",
            "state",
            "pincode",
            "contact_person",
            "phone",
            "email",
            "capacity",
            "exam_mode",
            "status",
            "instructions",
        ]

        widgets = {
            "centre_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: TVM-EC-001",
            }),
            "centre_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter centre name",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter full address",
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter city",
            }),
            "state": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter state",
            }),
            "pincode": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter PIN code",
            }),
            "contact_person": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Contact person's name",
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Contact number",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "example@company.com",
            }),
            "capacity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
            }),
            "exam_mode": forms.Select(attrs={
                "class": "form-control",
            }),
            "status": forms.Select(attrs={
                "class": "form-control",
            }),
            "instructions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional exam-centre instructions",
            }),
        }

    def clean_centre_code(self):
        return self.cleaned_data["centre_code"].strip().upper()

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()

        if not phone:
            raise forms.ValidationError(
                "Please enter a contact number."
            )

        return phone

class HallTicketForm(forms.ModelForm):
    class Meta:
        model = HallTicket
        fields = [
            "application",
            "hall_ticket_number",
            "student_name",
            "student_id",
            "exam_name",
            "exam_date",
            "start_time",
            "end_time",
            "centre_name",
            "venue",
            "seat_number",
            "status",
        ]

        widgets = {
            "application": forms.Select(attrs={
                "class": "form-control",
            }),
            "hall_ticket_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank to generate automatically",
            }),
            "student_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter student name",
            }),
            "student_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter student ID",
            }),
            "exam_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter examination name",
            }),
            "exam_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "start_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
            "end_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
            "centre_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Examination centre",
            }),
            "venue": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter the examination venue address",
            }),
            "seat_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter seat number",
            }),
            "status": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            self.add_error(
                "end_time",
                "End time must be later than start time.",
            )

        return cleaned_data



class ExaminationResultFilterForm(forms.Form):
    registration_number = forms.CharField(
        required=False,
        label="Registration Number",
        widget=forms.TextInput(attrs={
            "placeholder": "Enter registration number",
            "class": "form-control",
        }),
    )

    result_status = forms.ChoiceField(
        required=False,
        label="Result Status",
        choices=[
            ("", "All Results"),
            ("Pass", "Pass"),
            ("Fail", "Fail"),
            ("Absent", "Absent"),
            ("Withheld", "Withheld"),
            ("Incomplete", "Incomplete"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    publication_status = forms.ChoiceField(
        required=False,
        label="Publication Status",
        choices=[
            ("", "All Publication Statuses"),
            ("Draft", "Draft"),
            ("Approved", "Approved"),
            ("Published", "Published"),
            ("Withheld", "Withheld"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )