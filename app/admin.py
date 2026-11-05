
from django.contrib import admin

from .models import FeeStructure, FeeInstallment, FeePayment, Invoice

from .models import (
    CourseCategory,
    Course,
    Batch,
    Enquiry,
    CounsellingRecord,
    Student,
    Admission,
    AdmissionDocument,
    AdmissionStatusHistory,
)


# =========================================================
# COURSE CATEGORY ADMIN
# =========================================================

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category_type",
        "is_active",
        "created_at",
    )

    list_filter = (
        "category_type",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = ("name",)


# =========================================================
# COURSE ADMIN
# =========================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "category",
        "course_type",
        "duration",
        "duration_unit",
        "fee",
        "status",
    )

    list_filter = (
        "category",
        "course_type",
        "status",
    )

    search_fields = (
        "name",
        "code",
        "description",
    )

    ordering = ("name",)


# =========================================================
# BATCH ADMIN
# =========================================================

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "course",
        "start_date",
        "end_date",
        "max_capacity",
        "delivery_mode",
        "status",
    )

    list_filter = (
        "status",
        "delivery_mode",
        "course",
    )

    search_fields = (
        "name",
        "code",
        "course__name",
    )

    ordering = ("-start_date",)


# =========================================================
# COUNSELLING INLINE
# =========================================================

class CounsellingRecordInline(admin.TabularInline):
    model = CounsellingRecord
    extra = 0

    fields = (
        "counsellor",
        "counselling_status",
        "next_followup_date",
        "remarks",
        "counselling_date",
    )


# =========================================================
# ENQUIRY ADMIN
# =========================================================

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "enquiry_id",
        "student_name",
        "mobile",
        "email",
        "course_interested",
        "lead_source",
        "assigned_counsellor",
        "status",
        "followup_date",
    )

    list_filter = (
        "status",
        "lead_source",
        "course_interested",
        "assigned_counsellor",
        "enquiry_date",
    )

    search_fields = (
        "enquiry_id",
        "student_name",
        "mobile",
        "email",
        "college",
    )

    inlines = [
        CounsellingRecordInline,
    ]

    ordering = ("-enquiry_date",)


# =========================================================
# COUNSELLING RECORD ADMIN
# =========================================================

@admin.register(CounsellingRecord)
class CounsellingRecordAdmin(admin.ModelAdmin):
    list_display = (
        "enquiry",
        "counsellor",
        "counselling_status",
        "next_followup_date",
        "counselling_date",
    )

    list_filter = (
        "counselling_status",
        "counsellor",
        "counselling_date",
    )

    search_fields = (
        "enquiry__student_name",
        "enquiry__enquiry_id",
        "remarks",
    )

    ordering = ("-counselling_date",)


# =========================================================
# STUDENT ADMIN
# =========================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "full_name",
        "mobile",
        "email",
        "highest_qualification",
        "is_active",
    )

    list_filter = (
        "is_active",
        "gender",
    )

    search_fields = (
        "student_id",
        "full_name",
        "mobile",
        "email",
        "college",
    )

    ordering = ("full_name",)


# =========================================================
# ADMISSION DOCUMENT INLINE
# =========================================================

class AdmissionDocumentInline(admin.TabularInline):
    model = AdmissionDocument
    extra = 0


# =========================================================
# ADMISSION STATUS HISTORY INLINE
# =========================================================

class AdmissionStatusHistoryInline(admin.TabularInline):
    model = AdmissionStatusHistory
    extra = 0

    fields = (
        "previous_status",
        "new_status",
        "remarks",
        "changed_by",
        "created_at",
    )

    readonly_fields = (
        "previous_status",
        "new_status",
        "remarks",
        "changed_by",
        "created_at",
    )


# =========================================================
# ADMISSION ADMIN
# =========================================================

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = (
        "admission_number",
        "student",
        "course",
        "batch",
        "final_payable_amount",
        "amount_paid",
        "payment_status",
        "admission_status",
        "admission_date",
    )

    list_filter = (
        "admission_status",
        "payment_status",
        "course",
        "delivery_mode",
        "admission_date",
    )

    search_fields = (
        "admission_number",
        "student__full_name",
        "student__student_id",
        "student__mobile",
    )

    inlines = [
        AdmissionDocumentInline,
        AdmissionStatusHistoryInline,
    ]

    ordering = ("-admission_date",)


# =========================================================
# ADMISSION DOCUMENT ADMIN
# =========================================================

@admin.register(AdmissionDocument)
class AdmissionDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "admission",
        "document_name",
        "is_mandatory",
        "verification_status",
        "verified_by",
        "verified_at",
    )

    list_filter = (
        "verification_status",
        "is_mandatory",
        "document_name",
    )

    search_fields = (
        "admission__admission_number",
        "admission__student__full_name",
    )


# =========================================================
# ADMISSION STATUS HISTORY ADMIN
# =========================================================

@admin.register(AdmissionStatusHistory)
class AdmissionStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "admission",
        "previous_status",
        "new_status",
        "changed_by",
        "created_at",
    )

    list_filter = (
        "new_status",
        "created_at",
    )

    search_fields = (
        "admission__admission_number",
        "admission__student__full_name",
    )

    readonly_fields = (
        "admission",
        "previous_status",
        "new_status",
        "remarks",
        "changed_by",
        "created_at",
    )

    ordering = ("-created_at",)





@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("course", "course_fee", "discount", "final_amount")
    search_fields = ("course",)


@admin.register(FeeInstallment)
class FeeInstallmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "installment_number",
        "amount",
        "amount_paid",
        "due_date",
    )
    list_filter = ("due_date",)
    search_fields = ("student", "course", "batch")


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number",
        "student",
        "amount",
        "payment_date",
        "payment_mode",
        "status",
    )
    list_filter = ("status", "payment_mode", "payment_date")
    search_fields = ("receipt_number", "student", "transaction_id")
    readonly_fields = ("receipt_number", "created_at")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "student",
        "invoice_date",
        "total_amount",
        "paid_amount",
    )
    search_fields = ("invoice_number", "student")
