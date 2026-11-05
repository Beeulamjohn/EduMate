from decimal import Decimal
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import RegexValidator


class CourseCategory(models.Model):
    TYPE_CHOICES = [
        ("Technical", "Technical Courses"),
        ("Non-Technical", "Non-Technical Courses"),
    ]

    name = models.CharField(max_length=120, unique=True)
    category_type = models.CharField(
        max_length=50, choices=TYPE_CHOICES, default="Technical"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Course Categories"
        ordering = ["category_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.category_type})"


# ==========================================================
# COURSE
# ==========================================================
class Course(models.Model):
    STATUS_CHOICES = [("Active", "Active"), ("Inactive", "Inactive")]
    DURATION_UNIT_CHOICES = [
        ("Days", "Days"),
        ("Months", "Months"),
        ("Years", "Years"),
        ("Hours", "Hours"),
    ]
    COURSE_TYPE_CHOICES = [
        ("Certification", "Certification"),
        ("Diploma", "Diploma"),
        ("Advanced Diploma", "Advanced Diploma"),
        ("Fast Track", "Fast Track / Boot Camp"),
        ("Internship Program", "Internship Program"),
        ("Master Program", "Master Program"),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(
        CourseCategory, on_delete=models.PROTECT, related_name="courses"
    )
    course_type = models.CharField(
        max_length=50, choices=COURSE_TYPE_CHOICES, default="Certification"
    )
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(
        default=3, validators=[MinValueValidator(1)],
        help_text="Duration value, e.g. 3, 6, or 45",
    )
    duration_unit = models.CharField(
        max_length=20, choices=DURATION_UNIT_CHOICES, default="Months"
    )
    fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("25000.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    available_delivery_modes = models.CharField(
        max_length=150,
        default="Online, Offline, Hybrid",
        help_text="Comma-separated delivery modes, e.g. Online, Offline, Hybrid",
    )
    assigned_trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trainer_courses",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def formatted_duration(self):
        return f"{self.duration} {self.duration_unit}"


# ==========================================================
# BATCH
# ==========================================================
class Batch(models.Model):
    STATUS_CHOICES = [
        ("Upcoming", "Upcoming"),
        ("Ongoing", "Ongoing"),
        ("Completed", "Completed"),
        ("Inactive", "Inactive"),
    ]
    DELIVERY_MODE_CHOICES = [
        ("Online", "Online"),
        ("Offline", "Offline"),
        ("Hybrid", "Hybrid"),
        ("Recorded", "Recorded"),
        ("Live", "Live Interactive"),
    ]

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=60, unique=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="batches")
    start_date = models.DateField()
    end_date = models.DateField()
    assigned_trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trainer_batches",
    )
    max_capacity = models.PositiveIntegerField(
        default=30, validators=[MinValueValidator(1)]
    )
    delivery_mode = models.CharField(
        max_length=30, choices=DELIVERY_MODE_CHOICES, default="Offline"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Upcoming")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Batches"
        ordering = ["-start_date"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

    def __str__(self):
        return f"{self.name} [{self.code}] - {self.course.name}"

    @property
    def current_student_count(self):
        return self.admissions.filter(
            admission_status__in=["Confirmed", "Verification Completed"]
        ).count()

    @property
    def available_seats(self):
        return max(0, self.max_capacity - self.current_student_count)

    @property
    def is_full(self):
        return self.current_student_count >= self.max_capacity

    @property
    def can_enroll(self):
        return self.status in ["Upcoming", "Ongoing"] and not self.is_full


# ==========================================================
# ENQUIRY
# ==========================================================
class Enquiry(models.Model):
    LEAD_SOURCE_CHOICES = [
        ("Website", "Website"),
        ("Google", "Google Search"),
        ("Instagram", "Instagram"),
        ("Facebook", "Facebook"),
        ("WhatsApp", "WhatsApp"),
        ("Referral", "Referral"),
        ("Walk-in", "Walk-in"),
        ("College", "College Campus"),
        ("Exhibition/Event", "Exhibition / Event"),
        ("Existing Student", "Existing Student"),
    ]
    STATUS_CHOICES = [
        ("New", "New"),
        ("Contacted", "Contacted"),
        ("Counselling Completed", "Counselling Completed"),
        ("Interested", "Interested"),
        ("Follow-up", "Follow-up Due"),
        ("Admission Confirmed", "Admission Confirmed"),
        ("Not Interested", "Not Interested"),
    ]

    enquiry_id = models.CharField(max_length=30, unique=True, editable=False)
    student_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=25)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    qualification = models.CharField(max_length=150, blank=True)
    college = models.CharField(max_length=200, blank=True)
    course_interested = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="enquiries",
    )
    course_type = models.CharField(max_length=50, blank=True)
    lead_source = models.CharField(
        max_length=50, choices=LEAD_SOURCE_CHOICES, default="Website"
    )
    assigned_counsellor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_enquiries",
    )
    enquiry_date = models.DateField(default=timezone.localdate)
    followup_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="New")
    is_converted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Enquiries"
        ordering = ["-created_at"]

    def __str__(self):
        course_name = self.course_interested.name if self.course_interested else "Course not selected"
        return f"{self.enquiry_id} - {self.student_name} ({course_name})"

    def save(self, *args, **kwargs):
        if not self.enquiry_id:
            year = timezone.localdate().year
            prefix = f"ENQ-{year}-"
            # Retry if another request generates the same ID at the same time.
            for _ in range(5):
                last_id = (
                    Enquiry.objects.filter(enquiry_id__startswith=prefix)
                    .order_by("-enquiry_id")
                    .values_list("enquiry_id", flat=True)
                    .first()
                )
                try:
                    next_number = int(last_id.rsplit("-", 1)[-1]) + 1 if last_id else 1
                except (ValueError, IndexError):
                    next_number = 1
                self.enquiry_id = f"{prefix}{next_number:05d}"
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.enquiry_id = ""
            raise IntegrityError("Could not generate a unique enquiry ID. Please try again.")
        return super().save(*args, **kwargs)

    @property
    def name(self):
        """Compatibility property for templates expecting enquiry.name."""
        return self.student_name

    @property
    def follow_up_date(self):
        """Compatibility property for templates; ORM filters must use followup_date."""
        return self.followup_date

    @property
    def counsellor(self):
        return self.assigned_counsellor

    @property
    def is_followup_overdue(self):
        return bool(
            self.followup_date
            and self.followup_date < timezone.localdate()
            and self.status in ["New", "Contacted", "Interested", "Follow-up"]
        )

    @property
    def is_followup_today(self):
        return self.followup_date == timezone.localdate() if self.followup_date else False


# ==========================================================
# COUNSELLING RECORD
# ==========================================================

class CounsellingRecord(models.Model):
    STATUS_CHOICES = Enquiry.STATUS_CHOICES

    enquiry = models.ForeignKey(
        Enquiry,
        on_delete=models.CASCADE,
        related_name="counselling_records",
    )

    counsellor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counselling_sessions",
    )

    student_requirements = models.TextField(blank=True)
    career_objective = models.TextField(blank=True)

    recommended_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counselling_recommendations",
    )

    fee_discussion = models.TextField(blank=True)

    scholarship_details = models.CharField(
        max_length=200,
        blank=True,
    )

    counselling_status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default="Counselling Completed",
    )

    next_followup_date = models.DateField(
        null=True,
        blank=True,
    )

    remarks = models.TextField(blank=True)

    counselling_date = models.DateTimeField(
        default=timezone.now,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-counselling_date"]
        verbose_name = "Counselling Record"
        verbose_name_plural = "Counselling Records"

    def __str__(self):
        return (
            f"Counselling for {self.enquiry.student_name} "
            f"on {self.counselling_date:%Y-%m-%d}"
        )

    @property
    def status(self):
        return self.counselling_status

    @property
    def follow_up_date(self):
        return self.next_followup_date

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Synchronize the related enquiry after saving counselling.
        Enquiry.objects.filter(pk=self.enquiry_id).update(
            status=self.counselling_status,
            followup_date=self.next_followup_date,
            updated_at=timezone.now(),
        )


# Backward compatibility for existing imports.
Counselling = CounsellingRecord

# ==========================================================
# STUDENT
# ==========================================================
class Student(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    student_id = models.CharField(max_length=35, unique=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="student_profile",
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=25)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    highest_qualification = models.CharField(max_length=150, blank=True)
    university = models.CharField(max_length=200, blank=True)
    college = models.CharField(max_length=200, blank=True)
    passing_year = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1950), MaxValueValidator(2100)]
    )
    percentage_cgpa = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to="students/photos/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            year = timezone.localdate().year
            prefix = f"SC-STU-{year}-"
            for _ in range(5):
                last_id = (
                    Student.objects.filter(student_id__startswith=prefix)
                    .order_by("-student_id")
                    .values_list("student_id", flat=True)
                    .first()
                )
                try:
                    next_number = int(last_id.rsplit("-", 1)[-1]) + 1 if last_id else 1
                except (ValueError, IndexError):
                    next_number = 1
                self.student_id = f"{prefix}{next_number:05d}"
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.student_id = ""
            raise IntegrityError("Could not generate a unique student ID. Please try again.")
        return super().save(*args, **kwargs)


# ==========================================================
# ADMISSION
# ==========================================================
class Admission(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Partially Paid", "Partially Paid"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    ]
    ADMISSION_STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Documents Pending", "Documents Pending"),
        ("Verification Completed", "Verification Completed"),
        ("Confirmed", "Admission Confirmed"),
        ("Cancelled", "Cancelled"),
    ]
    DELIVERY_MODE_CHOICES = [
        ("Online", "Online"),
        ("Offline", "Offline"),
        ("Hybrid", "Hybrid"),
        ("Recorded", "Recorded"),
        ("Live", "Live Interactive"),
    ]

    admission_number = models.CharField(max_length=40, unique=True, editable=False)
    enquiry = models.OneToOneField(
        Enquiry, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="admission",
    )
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="admissions")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="admissions")
    batch = models.ForeignKey(
        Batch, null=True, blank=True, on_delete=models.SET_NULL, related_name="admissions"
    )
    delivery_mode = models.CharField(
        max_length=30, choices=DELIVERY_MODE_CHOICES, default="Offline"
    )
    admission_date = models.DateField(default=timezone.localdate)
    course_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    scholarship_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    final_payable_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    outstanding_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    payment_status = models.CharField(
        max_length=30, choices=PAYMENT_STATUS_CHOICES, default="Pending"
    )
    admission_status = models.CharField(
        max_length=35, choices=ADMISSION_STATUS_CHOICES, default="Draft"
    )
    counsellor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="admissions_handled",
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.admission_number} - {self.student.full_name} ({self.course.name})"

    @classmethod
    def generate_admission_number(cls):
        year = timezone.localdate().year
        prefix = f"SC-ADM-{year}-"
        last_id = (
            cls.objects.filter(admission_number__startswith=prefix)
            .order_by("-admission_number")
            .values_list("admission_number", flat=True)
            .first()
        )
        try:
            next_number = int(last_id.rsplit("-", 1)[-1]) + 1 if last_id else 1
        except (ValueError, IndexError):
            next_number = 1
        return f"{prefix}{next_number:05d}"

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        if self.course_fee is not None and self.scholarship_discount is not None:
            if self.scholarship_discount > self.course_fee:
                errors["scholarship_discount"] = "Discount cannot exceed the course fee."
        if self.amount_paid is not None and self.final_payable_amount is not None:
            if self.amount_paid > self.final_payable_amount:
                errors["amount_paid"] = "Amount paid cannot exceed the final payable amount."
        if self.batch_id and self.course_id and self.batch.course_id != self.course_id:
            errors["batch"] = "Selected batch does not belong to the selected course."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.course_fee = Decimal(str(self.course_fee or "0.00"))
        self.scholarship_discount = Decimal(str(self.scholarship_discount or "0.00"))
        self.amount_paid = Decimal(str(self.amount_paid or "0.00"))

        if self.course_fee < 0 or self.scholarship_discount < 0 or self.amount_paid < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError("Fee, discount, and amount paid cannot be negative.")
        if self.scholarship_discount > self.course_fee:
            from django.core.exceptions import ValidationError
            raise ValidationError({"scholarship_discount": "Discount cannot exceed the course fee."})

        self.final_payable_amount = self.course_fee - self.scholarship_discount
        if self.amount_paid > self.final_payable_amount:
            from django.core.exceptions import ValidationError
            raise ValidationError({"amount_paid": "Amount paid cannot exceed the final payable amount."})
        self.outstanding_balance = self.final_payable_amount - self.amount_paid

        if self.final_payable_amount == 0 or self.amount_paid >= self.final_payable_amount:
            self.payment_status = "Paid"
        elif self.amount_paid > 0:
            self.payment_status = "Partially Paid"
        else:
            self.payment_status = "Pending"

        if not self.admission_number:
            # Retry on the unlikely event of a simultaneous duplicate number.
            for _ in range(5):
                self.admission_number = self.generate_admission_number()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.admission_number = ""
            raise IntegrityError("Could not generate a unique admission number. Please try again.")
        return super().save(*args, **kwargs)

    @property
    def has_pending_documents(self):
        return self.documents.filter(is_mandatory=True).exclude(
            verification_status="Verified"
        ).exists()

    @property
    def all_mandatory_documents_verified(self):
        mandatory_docs = self.documents.filter(is_mandatory=True)
        return mandatory_docs.exists() and not mandatory_docs.exclude(
            verification_status="Verified"
        ).exists()

    # Compatibility display properties; use admission_status in ORM queries.
    @property
    def status(self):
        return "Admission Confirmed" if self.admission_status == "Confirmed" else self.admission_status

    @property
    def name(self):
        return self.student.full_name


# ==========================================================
# ADMISSION DOCUMENT
# ==========================================================
class AdmissionDocument(models.Model):
    DOCUMENT_TYPES = [
        ("Student Photo", "Student Photo"),
        ("Identity Proof", "Identity Proof (Aadhaar / Passport / Voter ID)"),
        ("Educational Certificate", "Educational Certificate / Degree / Marksheet"),
        ("Resume", "Resume / Curriculum Vitae"),
        ("Other Documents", "Other Documents (Income / Caste / Migration)"),
    ]
    VERIFICATION_STATUS_CHOICES = [
        ("Not Uploaded", "Not Uploaded"),
        ("Pending Verification", "Pending Verification"),
        ("Verified", "Verified"),
        ("Rejected", "Rejected"),
    ]

    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name="documents")
    document_name = models.CharField(max_length=60, choices=DOCUMENT_TYPES)
    document_file = models.FileField(
        upload_to="admissions/documents/%Y/%m/", blank=True, null=True
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    is_mandatory = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=30, choices=VERIFICATION_STATUS_CHOICES, default="Pending Verification"
    )
    verification_remarks = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="verified_documents",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["document_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["admission", "document_name"],
                name="unique_document_type_per_admission",
            )
        ]

    def save(self, *args, **kwargs):
        if self.verification_status == "Verified" and not self.verified_at:
            self.verified_at = timezone.now()
        elif self.verification_status != "Verified":
            self.verified_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document_name} for {self.admission.admission_number}"


# ==========================================================
# ADMISSION STATUS HISTORY
# ==========================================================
class AdmissionStatusHistory(models.Model):
    admission = models.ForeignKey(
        Admission, on_delete=models.CASCADE, related_name="status_history"
    )
    previous_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    remarks = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="admission_status_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Admission Status History"
        verbose_name_plural = "Admission Status History"

    def __str__(self):
        return f"{self.admission.admission_number}: {self.previous_status} -> {self.new_status}"

class AdmissionConfirmation(models.Model):
    admission = models.OneToOneField(
        Admission,
        on_delete=models.PROTECT,
        related_name="confirmation",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="admissions_confirmed",
    )
    confirmed_at = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-confirmed_at"]

    def __str__(self):
        return f"Confirmation: {self.admission.admission_number}"

hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Enter a valid color code, for example #2563eb.",
)


class AdmissionSettings(models.Model):

    # GENERAL SETTINGS
    institution_name = models.CharField(
        max_length=200,
        default="SciPy Technologies",
    )

    contact_email = models.EmailField(
        blank=True,
        default="",
    )

    contact_phone = models.CharField(
        max_length=25,
        blank=True,
        default="",
    )

    # ADMISSION SETTINGS
    admission_number_prefix = models.CharField(
        max_length=30,
        default="SC-ADM",
    )

    ADMISSION_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
    ]

    default_admission_status = models.CharField(
        max_length=30,
        choices=ADMISSION_STATUS_CHOICES,
        default="Pending",
    )

    # DOCUMENT SETTINGS
    require_document_verification = models.BooleanField(
        default=True,
    )

    # APPEARANCE SETTINGS
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("system", "System Default"),
    ]

    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default="light",
    )

    primary_color = models.CharField(
        max_length=7,
        default="#2563eb",
        validators=[hex_color_validator],
    )

    accent_color = models.CharField(
        max_length=7,
        default="#0891c2",
        validators=[hex_color_validator],
    )

    # SYSTEM INFORMATION
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Admission Settings"
        verbose_name_plural = "Admission Settings"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.institution_name} - Admission Settings"



class FeeStructure(models.Model):
    course = models.CharField(max_length=150, unique=True)

    course_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    registration_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    admission_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    material_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    exam_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    project_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    certification_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    other_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def final_amount(self):
        subtotal = (
            self.course_fee
            + self.registration_fee
            + self.admission_fee
            + self.material_fee
            + self.exam_fee
            + self.project_fee
            + self.certification_fee
            + self.other_fee
        )
        discounted = max(Decimal("0.00"), subtotal - self.discount)
        tax = discounted * self.tax_percentage / Decimal("100")
        return (discounted + tax).quantize(Decimal("0.01"))

    def __str__(self):
        return self.course


class FeeInstallment(models.Model):
    student = models.CharField(max_length=150)
    course = models.CharField(max_length=150, blank=True)
    batch = models.CharField(max_length=100, blank=True)
    counsellor = models.CharField(max_length=150, blank=True)

    installment_number = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    due_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def pending_amount(self):
        return max(Decimal("0.00"), self.amount - self.amount_paid)

    @property
    def status(self):
        if self.pending_amount <= 0:
            return "Paid"
        if self.due_date and self.due_date < timezone.localdate():
            return "Overdue"
        return "Pending"

    def __str__(self):
        return f"{self.student} - Installment {self.installment_number}"


class FeePayment(models.Model):
    PAYMENT_MODES = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("card", "Card"),
        ("payment_gateway", "Payment Gateway"),
        ("cheque", "Cheque"),
        ("other", "Other"),
    ]

    PAYMENT_STATUSES = [
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
        ("reversed", "Reversed"),
    ]

    receipt_number = models.CharField(
        max_length=50, unique=True, blank=True
    )
    installment = models.ForeignKey(
        FeeInstallment,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    student = models.CharField(max_length=150)
    course = models.CharField(max_length=150, blank=True)

    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"))
        ]
    )
    payment_date = models.DateField(default=timezone.localdate)
    payment_mode = models.CharField(
        max_length=30, choices=PAYMENT_MODES
    )
    transaction_id = models.CharField(max_length=150, blank=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_fee_payments",
        null=True,
        blank=True,
    )
    remarks = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = (
                f"FEE-{timezone.now():%Y%m%d%H%M%S%f}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


class Invoice(models.Model):
    invoice_number = models.CharField(
        max_length=50, unique=True, blank=True
    )
    student = models.CharField(max_length=150)
    invoice_date = models.DateField(default=timezone.localdate)

    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    paid_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    pdf_file = models.FileField(
        upload_to="fee_invoices/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def balance_amount(self):
        return max(Decimal("0.00"), self.total_amount - self.paid_amount)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = (
                f"INV-{timezone.now():%Y%m%d%H%M%S%f}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number


class FeeReminder(models.Model):

    STATUS_PENDING = "Pending"
    STATUS_SENT = "Sent"
    STATUS_COMPLETED = "Completed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_COMPLETED, "Completed"),
    ]

    admission = models.ForeignKey(
    "app.Admission",
    on_delete=models.PROTECT,
    related_name="fee_reminders",
)

    reminder_date = models.DateField(
        default=timezone.localdate,
    )

    due_date = models.DateField()

    message = models.TextField(
        help_text="Enter the fee reminder message.",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_fee_reminders",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["status", "due_date", "-created_at"]
        verbose_name = "Fee Reminder"
        verbose_name_plural = "Fee Reminders"

    def __str__(self):
        return (
            f"Reminder: {self.admission.admission_number} "
            f"- {self.get_status_display()}"
        )

    @property
    def outstanding_balance(self):
        """Read the balance from the existing admission record."""
        return self.admission.outstanding_balance

    @property
    def is_overdue(self):
        return (
            self.due_date < timezone.localdate()
            and self.status != self.STATUS_COMPLETED
            and self.outstanding_balance > 0
        )



class DiplomaExam(models.Model):
    exam_name = models.CharField(max_length=200)
    course_name = models.CharField(max_length=200)
    exam_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    exam_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["exam_date"]

    def __str__(self):
        return f"{self.exam_name} - {self.course_name}"

    @property
    def registration_open(self):
        return (
            self.is_active
            and timezone.now() <= self.registration_deadline
        )


class DiplomaExamEligibility(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="diploma_exam_eligibility",
    )
    exam = models.ForeignKey(
        DiplomaExam,
        on_delete=models.PROTECT,
        related_name="eligibility_records",
    )
    is_eligible = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_diploma_eligibilities",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "exam"],
                name="unique_diploma_eligibility",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} - {self.exam}"


class DiplomaExamRegistration(models.Model):
    REGISTRATION_CHOICES = [
        ("registered", "Registered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="diploma_exam_registrations",
    )
    exam = models.ForeignKey(
        DiplomaExam,
        on_delete=models.PROTECT,
        related_name="registrations",
    )
    registration_number = models.CharField(
        max_length=40,
        unique=True,
        blank=True,
    )
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    registration_status = models.CharField(
        max_length=20,
        choices=REGISTRATION_CHOICES,
        default="registered",
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="pending",
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "exam"],
                name="unique_diploma_registration",
            )
        ]
        ordering = ["-registered_at"]

    def save(self, *args, **kwargs):
        if not self.registration_number:
            self.registration_number = (
                f"DER-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.registration_number

class DiplomaExamPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("online", "Online"),
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("other", "Other"),
    ]

    registration = models.ForeignKey(
        "DiplomaExamRegistration",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="online",
    )

    transaction_reference = models.CharField(
        max_length=150,
        blank=True,
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
        db_index=True,
    )

    verification_notes = models.TextField(blank=True)

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_diploma_exam_payments",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Payment #{self.pk} - "
            f"{self.registration} - ₹{self.amount}"
        )

# ==========================================================
# EXAMINATION CENTRE
# ==========================================================
class ExaminationCentre(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Examination Centre"
        verbose_name_plural = "Examination Centres"

    def __str__(self):
        return f"{self.name} - {self.city}"


class Examination(models.Model):

    EXAM_MODE_CHOICES = [
        ("ONLINE", "Online"),
        ("OFFLINE", "Offline"),
        ("HYBRID", "Hybrid"),
    ]

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SCHEDULED", "Scheduled"),
        ("ONGOING", "Ongoing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    exam_code = models.CharField(
        max_length=30,
        unique=True
    )

    exam_name = models.CharField(max_length=200)

    # Replace "app.Course" if your Course model is in another app.
    course = models.ForeignKey(
        "app.Course",
        on_delete=models.PROTECT,
        related_name="examinations",
    )

    centre = models.ForeignKey(
        ExaminationCentre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="examinations",
    )

    exam_date = models.DateTimeField()

    exam_mode = models.CharField(
        max_length=10,
        choices=EXAM_MODE_CHOICES,
        default="OFFLINE",
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_examinations",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-exam_date"]
        verbose_name = "Examination"
        verbose_name_plural = "Examinations"

    def __str__(self):
        return f"{self.exam_code} - {self.exam_name}"

    

class ExaminationSubject(models.Model):
    examination = models.ForeignKey(
        "app.Examination",
        on_delete=models.CASCADE,
        related_name="subjects",
    )

    subject_name = models.CharField(max_length=150)

    subject_code = models.CharField(max_length=30)

    max_marks = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["subject_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["examination", "subject_code"],
                name="unique_subject_code_per_examination",
            )
        ]
        verbose_name = "Examination Subject"
        verbose_name_plural = "Examination Subjects"

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"


# ==========================================================
# EXAM APPLICATION
# ==========================================================
class ExamApplication(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Cancelled", "Cancelled"),
    ]
    ELIGIBILITY_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Eligible", "Eligible"),
        ("Not Eligible", "Not Eligible"),
    ]

    registration_number = models.CharField(max_length=40, unique=True, blank=True)
    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name="exam_applications"
    )
    examination = models.ForeignKey(
        Examination, on_delete=models.PROTECT, related_name="applications"
    )
    application_date = models.DateField(default=timezone.localdate)
    academic_session = models.CharField(max_length=50, blank=True)
    eligibility_status = models.CharField(
        max_length=20, choices=ELIGIBILITY_STATUS_CHOICES, default="Pending"
    )
    eligibility_remarks = models.TextField(blank=True)
    eligibility_checked_at = models.DateTimeField(null=True, blank=True)
    eligibility_checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="eligibility_checks"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Pending"
    )
    status_remarks = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reviewed_exam_applications"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "examination"],
                name="unique_student_exam_application"
            )
        ]

    def __str__(self):
        return f"{self.registration_number} - {self.student.full_name}"

    @classmethod
    def generate_registration_number(cls):
        year = timezone.localdate().year
        prefix = f"SC-EXAM-{year}-"
        last = (
            cls.objects.filter(registration_number__startswith=prefix)
            .order_by("-registration_number")
            .values_list("registration_number", flat=True)
            .first()
        )
        try:
            next_num = int(last.rsplit("-", 1)[-1]) + 1 if last else 1
        except (ValueError, IndexError):
            next_num = 1
        return f"{prefix}{next_num:06d}"

    def save(self, *args, **kwargs):
        if not self.registration_number:
            for _ in range(5):
                self.registration_number = self.generate_registration_number()
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.registration_number = ""
            raise IntegrityError("Could not generate a unique exam registration number.")
        return super().save(*args, **kwargs)

    @property
    def student_name(self):
        return self.student.full_name

    @property
    def student_id(self):
        return self.student.student_id

    @property
    def diploma_name(self):
        return self.examination.course.name

    @property
    def payment_status(self):
        payment = self.exam_payment if hasattr(self, 'exam_payment') else None
        if not payment:
            try:
                payment = self.examapplicationpayment
            except Exception:
                return "Pending"
        return payment.status if payment else "Pending"


# ==========================================================
# EXAM APPLICATION PAYMENT
# ==========================================================
class ExamApplicationPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("Cash", "Cash"),
        ("Bank Transfer", "Bank Transfer"),
        ("UPI", "UPI"),
        ("Card", "Card"),
        ("Cheque", "Cheque"),
        ("Other", "Other"),
    ]

    application = models.OneToOneField(
        ExamApplication, on_delete=models.PROTECT,
        related_name="examapplicationpayment"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(
        max_length=30, choices=PAYMENT_METHOD_CHOICES, blank=True
    )
    transaction_reference = models.CharField(max_length=150, blank=True)
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending"
    )
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="collected_exam_payments"
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment for {self.application.registration_number} - {self.status}"


# ==========================================================
# HALL TICKET
# ==========================================================
class HallTicket(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Reissued", "Reissued"),
        ("Cancelled", "Cancelled"),
    ]

    hall_ticket_number = models.CharField(max_length=50, unique=True, blank=True)
    application = models.ForeignKey(
        ExamApplication, on_delete=models.PROTECT,
        related_name="hall_tickets"
    )
    issue_date = models.DateField(default=timezone.localdate)
    verification_code = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Active"
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="issued_hall_tickets"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.hall_ticket_number} - {self.application.student.full_name}"

    def save(self, *args, **kwargs):
        import uuid as _uuid
        if not self.hall_ticket_number:
            year = timezone.localdate().year
            self.hall_ticket_number = f"HT-{year}-{_uuid.uuid4().hex[:8].upper()}"
        if not self.verification_code:
            import hashlib
            self.verification_code = hashlib.sha256(
                f"{self.application_id}{self.issue_date}".encode()
            ).hexdigest()[:16].upper()
        super().save(*args, **kwargs)


# ==========================================================
# EXAMINATION MARK
# ==========================================================
class ExaminationMark(models.Model):
    EVAL_STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Approved", "Approved"),
    ]

    application = models.ForeignKey(
        ExamApplication,
        on_delete=models.PROTECT,
        related_name="marks",
    )

    subject = models.ForeignKey(
        ExaminationSubject,
        on_delete=models.PROTECT,
        related_name="marks",
    )

    marks_obtained = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    internal_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    practical_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    is_absent = models.BooleanField(default=False)

    examiner_remarks = models.TextField(blank=True)

    eval_status = models.CharField(
        max_length=20,
        choices=EVAL_STATUS_CHOICES,
        default="Draft",
    )

    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entered_marks",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_marks",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["application", "subject"]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "subject"],
                name="unique_mark_per_application_subject",
            )
        ]

    def __str__(self):
        return (
            f"{self.application.registration_number} - "
            f"{self.subject.subject_name}: {self.marks_obtained}"
        )

    def clean(self):
        super().clean()

        if self.is_absent:
            self.marks_obtained = Decimal("0.00")
            self.internal_marks = Decimal("0.00")
            self.practical_marks = Decimal("0.00")
            return

        if self.subject_id:
            maximum = Decimal(str(self.subject.max_marks))

            if self.marks_obtained > maximum:
                raise ValidationError({
                    "marks_obtained": (
                        f"Marks cannot exceed {maximum}."
                    )
                })

# ==========================================================
# EXAMINATION RESULT
# ==========================================================
class ExaminationResult(models.Model):
    RESULT_STATUS_CHOICES = [
        ("Pass", "Pass"),
        ("Fail", "Fail"),
        ("Absent", "Absent"),
        ("Withheld", "Withheld"),
        ("Incomplete", "Incomplete"),
    ]
    PUBLICATION_STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Approved", "Approved"),
        ("Published", "Published"),
        ("Withheld", "Withheld"),
    ]

    application = models.OneToOneField(
        ExamApplication, on_delete=models.PROTECT, related_name="result"
    )
    total_marks_obtained = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00")
    )
    total_max_marks = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    grade = models.CharField(max_length=5, blank=True)
    result_status = models.CharField(
        max_length=20, choices=RESULT_STATUS_CHOICES, default="Incomplete"
    )
    publication_status = models.CharField(
        max_length=20, choices=PUBLICATION_STATUS_CHOICES, default="Draft"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="published_results"
    )
    calculated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-calculated_at"]

    def __str__(self):
        return f"Result: {self.application.registration_number} - {self.result_status}"

    def calculate(self):
        """Recalculate totals and grade from approved marks."""
        marks_qs = self.application.marks.filter(eval_status="Approved")
        if not marks_qs.exists():
            return

        total_obtained = sum(
            m.marks_obtained for m in marks_qs if not m.is_absent
        )
        total_max = sum(m.subject.max_marks for m in marks_qs)
        self.total_marks_obtained = total_obtained
        self.total_max_marks = total_max
        self.percentage = (
            (total_obtained / total_max * 100).quantize(Decimal("0.01"))
            if total_max > 0 else Decimal("0.00")
        )

        # Determine pass/fail
        all_passed = all(
            (not m.is_absent and m.marks_obtained >= m.subject.passing_marks)
            for m in marks_qs
        )
        any_absent = any(m.is_absent for m in marks_qs)

        if any_absent:
            self.result_status = "Absent"
        elif all_passed:
            self.result_status = "Pass"
        else:
            self.result_status = "Fail"

        # Grade calculation
        pct = float(self.percentage)
        if pct >= 90:
            self.grade = "O"
        elif pct >= 75:
            self.grade = "A+"
        elif pct >= 60:
            self.grade = "A"
        elif pct >= 50:
            self.grade = "B"
        elif pct >= 40:
            self.grade = "C"
        else:
            self.grade = "F"

        self.save()


# ==========================================================
# CERTIFICATE
# ==========================================================
class Certificate(models.Model):
    CERT_TYPE_CHOICES = [
        ("Course Completion", "Course Completion"),
        ("Diploma", "Diploma"),
        ("Advanced Diploma", "Advanced Diploma"),
        ("Internship", "Internship"),
        ("Project", "Project"),
        ("Training", "Training"),
        ("Workshop", "Workshop"),
        ("Participation", "Participation"),
    ]
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Revoked", "Revoked"),
        ("Expired", "Expired"),
    ]

    certificate_number = models.CharField(max_length=60, unique=True, blank=True)
    certificate_type = models.CharField(
        max_length=40, choices=CERT_TYPE_CHOICES, default="Course Completion"
    )
    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name="certificates"
    )
    course = models.ForeignKey(
        Course, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="certificates"
    )
    exam_result = models.OneToOneField(
        ExaminationResult, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="certificate"
    )
    issue_date = models.DateField(default=timezone.localdate)
    completion_date = models.DateField(null=True, blank=True)
    duration_display = models.CharField(max_length=80, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Active"
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="issued_certificates"
    )
    revocation_reason = models.TextField(blank=True)
    qr_code = models.ImageField(
        upload_to="certificates/qr/", blank=True, null=True
    )
    pdf_file = models.FileField(
        upload_to="certificates/pdf/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.certificate_number} - {self.student.full_name}"

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            year = timezone.localdate().year
            prefix = f"SC-CERT-{year}-"
            last = (
                Certificate.objects.filter(certificate_number__startswith=prefix)
                .order_by("-certificate_number")
                .values_list("certificate_number", flat=True)
                .first()
            )
            try:
                next_num = int(last.rsplit("-", 1)[-1]) + 1 if last else 1
            except (ValueError, IndexError):
                next_num = 1
            self.certificate_number = f"{prefix}{next_num:06d}"
        super().save(*args, **kwargs)

    def generate_qr(self):
        """Generate a QR code pointing to the certificate verification URL."""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files.base import ContentFile
            from django.urls import reverse

            verify_url = f"/exam/certificate-verify/{self.certificate_number}/"
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(verify_url)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            buf = BytesIO()
            img.save(buf, format="PNG")
            self.qr_code.save(
                f"cert_{self.certificate_number}.png",
                ContentFile(buf.getvalue()),
                save=False,
            )
        except ImportError:
            pass

class DiplomaExamEligibility(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="diploma_exam_eligibilities",
    )

    exam = models.ForeignKey(
        "DiplomaExam",
        on_delete=models.CASCADE,
        related_name="eligibility_records",
    )

    is_eligible = models.BooleanField(default=False)

    remarks = models.TextField(blank=True)

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diploma_eligibility_verifications",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "exam"],
                name="unique_diploma_eligibility_per_student_exam",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.exam}"


class ExamFeePayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("Cash", "Cash"),
        ("UPI", "UPI"),
        ("Card", "Debit/Credit Card"),
        ("Bank Transfer", "Bank Transfer"),
        ("Razorpay", "Razorpay"),
        ("Cashfree", "Cashfree"),
        ("Other", "Other"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending Verification"),
        ("Verified", "Verified"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    ]

    application = models.ForeignKey(
        ExamApplication,
        on_delete=models.PROTECT,
        related_name="fee_payments",
    )

    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Total examination fee payable.",
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default="UPI",
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
    )

    payment_date = models.DateField(
        default=timezone.localdate,
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending",
    )

    remarks = models.TextField(blank=True)

    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entered_exam_fee_payments",
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_exam_fee_payments",
    )

    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Examination Fee Payment"
        verbose_name_plural = "Examination Fee Payments"

    def __str__(self):
        return (
            f"{self.application.registration_number} - "
            f"₹{self.amount_paid} - {self.status}"
        )

    @property
    def balance_amount(self):
        return max(
            Decimal("0.00"),
            self.fee_amount - self.amount_paid,
        )

    def clean(self):
        super().clean()
        errors = {}

        if self.amount_paid is not None and self.fee_amount is not None:
            if self.amount_paid > self.fee_amount:
                errors["amount_paid"] = (
                    "Amount paid cannot exceed the examination fee."
                )

        if self.status == "Verified" and self.amount_paid <= 0:
            errors["amount_paid"] = (
                "A payment must be greater than zero before verification."
            )

        if errors:
            raise ValidationError(errors)



class ExamSchedule(models.Model):
    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("ONGOING", "Ongoing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    examination = models.ForeignKey(
        "app.Examination",
        on_delete=models.PROTECT,
        related_name="schedules",
    )

    schedule_date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    venue = models.CharField(
        max_length=200,
        help_text="Enter the examination room, centre, or online venue.",
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="SCHEDULED",
    )

    instructions = models.TextField(
        blank=True,
        help_text="Optional instructions for students.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["schedule_date", "start_time"]
        verbose_name = "Exam Schedule"
        verbose_name_plural = "Exam Schedules"

    def clean(self):
        super().clean()

        if (
            self.start_time
            and self.end_time
            and self.end_time <= self.start_time
        ):
            raise ValidationError({
                "end_time": "End time must be later than start time."
            })

    def __str__(self):
        return (
            f"{self.examination.exam_name} - "
            f"{self.schedule_date}"
        )


class ExamCentre(models.Model):
    MODE_CHOICES = [
        ("OFFLINE", "Offline"),
        ("ONLINE", "Online"),
        ("HYBRID", "Hybrid"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    centre_code = models.CharField(
        max_length=30,
        unique=True,
    )
    centre_name = models.CharField(max_length=150)

    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    contact_person = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    capacity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    exam_mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default="OFFLINE",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    instructions = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["centre_name"]
        verbose_name = "Exam Centre"
        verbose_name_plural = "Exam Centres"

    def __str__(self):
        return f"{self.centre_code} - {self.centre_name}"

class HallTicket(models.Model):
    STATUS_CHOICES = [
        ("GENERATED", "Generated"),
        ("REVOKED", "Revoked"),
    ]

    # Optional during migration so existing records are not blocked.
    # Once the existing data is reconciled, you can make this required.
    application = models.OneToOneField(
        "ExamApplication",
        on_delete=models.PROTECT,
        related_name="hall_ticket",
        null=True,
        blank=True,
    )

    hall_ticket_number = models.CharField(
        max_length=60,
        unique=True,
        null=True,
        blank=True,
    )

    student_name = models.CharField(max_length=150, blank=True, default="")
    student_id = models.CharField(max_length=60, blank=True, default="")
    exam_name = models.CharField(max_length=200, blank=True, default="")

    exam_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    centre_name = models.CharField(max_length=200, blank=True, default="")
    venue = models.TextField(blank=True, default="")
    seat_number = models.CharField(max_length=30, blank=True, default="")

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="GENERATED",
    )

    # Keep the existing created_at field; do not rename it in this version.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.hall_ticket_number or f"Hall Ticket {self.pk}"