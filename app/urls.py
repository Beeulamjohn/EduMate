
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("features/", views.features, name="features"),
    path("about/", views.about, name="about"),
    path("benefits/", views.benefits, name="benefits"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),

    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("admissions/", views.admission_dashboard, name="admission_dashboard"),

    path(
        "enquiries/",
        views.enquiry_management,
        name="enquiry_management",
    ),
    path(
        "enquiries/add/",
        views.enquiry_create,
        name="enquiry_create",
    ),
    path(
        "enquiries/<int:pk>/edit/",
        views.enquiry_edit,
        name="enquiry_edit",
    ),
    path(
        "enquiries/<int:pk>/delete/",
        views.enquiry_delete,
        name="enquiry_delete",
    ),
      path(
        "counselling/",
        views.counselling_management,
        name="counselling_management",
    ),
    path(
        "counselling/add/",
        views.counselling_create,
        name="counselling_create",
    ),
    path(
        "counselling/<int:pk>/edit/",
        views.counselling_edit,
        name="counselling_edit",
    ),
    path(
        "counselling/<int:pk>/delete/",
        views.counselling_delete,
        name="counselling_delete",
    ),
     path(
        "admissions/register/",
        views.admission_registration,
        name="admission_registration",
    ),
    path(
        "admissions/",
        views.admission_register,
        name="admission_register",
    ),
    path(
        "admissions/<int:pk>/",
        views.admission_detail,
        name="admission_detail",
    ),
    path(
        "admissions/<int:pk>/documents/",
        views.document_verification,
        name="document_verification",
    ),
    path(
        "admissions/<int:pk>/confirm/",
        views.admission_confirmation,
        name="admission_confirmation",
    ),
    path("students/", views.student_list, name="student_list"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),

    path(
    "admission/reports/",
    views.admission_reports,
    name="admission_reports",
),
path(
    "admission/settings/",
    views.admission_settings,
    name="admission_settings",
),

path(
    "scheduling/",
    views.scheduling_dashboard,
    name="scheduling_dashboard",
),

path(
    "courses/",
    views.course_list,
    name="course_list",
),
path("batches/", views.batch_list, name="batch_list"),
    path(
        "fees/dashboard/",
        views.fee_dashboard,
        name="fee_dashboard",
    ),
    path(
        "fees/structure/create/",
        views.fee_structure_create,
        name="fee_structure_create",
    ),
    path(
    "fees/installments/create/",
    views.fee_installment_create,
    name="fee_installment_create",
),
    path(
        "fees/payments/create/",
        views.fee_payment_create,
        name="fee_payment_create",
    ),
    path(
        "fees/invoices/create/",
        views.fee_invoice_create,
        name="fee_invoice_create",
    ),
    path(
    "fees/outstanding/",
    views.outstanding_fees,
    name="outstanding_fees",
),
    path(
    "fees/reminders/",
    views.fee_reminders,
    name="fee_reminders",
    ),
    path("exam-application/", views.exam_application_dashboard, name="exam_application_dashboard"),
    path("result-verification/", views.result_verification, name="result_verification"),
    path("diploma-exams/", views.diploma_exam_management, name="diploma_exam_management"),
    path("diploma-exams/register/", views.diploma_exam_register, name="diploma_exam_register"),
    path(
        "diploma-exams/eligibility/",
        views.eligibility_verification,
        name="eligibility_verification",
    ),
    path(
        "diploma-exams/payments/<int:payment_id>/verify/",
        views.exam_payment_verification,
        name="exam_payment_verification",
    ),
     path(
        "examinations/",
        views.examination_management,
        name="examination_management",
    ),
    path(
        "examinations/add/",
        views.examination_create,
        name="examination_create",
    ),
    path(
        "examinations/<int:exam_id>/edit/",
        views.examination_edit,
        name="examination_edit",
    ),
    path(
        "examinations/<int:exam_id>/change-status/",
        views.examination_change_status,
        name="examination_change_status",
    ),
    path(
        "examination-marks/",
        views.examination_mark_management,
        name="examination_mark_management",
    ),
    path(
        "examination-marks/add/",
        views.examination_mark_create,
        name="examination_mark_create",
    ),
    path(
        "examination-marks/<int:mark_id>/edit/",
        views.examination_mark_edit,
        name="examination_mark_edit",
    ),
    path(
        "examination-marks/<int:mark_id>/submit/",
        views.examination_mark_submit,
        name="examination_mark_submit",
    ),
    path(
        "examination-marks/<int:mark_id>/approve/",
        views.examination_mark_approve,
        name="examination_mark_approve",
    ),

    path("hall-tickets/", views.hall_ticket_management, name="hall_ticket_management"),
    path("exam-results/", views.result_management, name="result_management"),
    path("certificates/", views.certificate_management, name="certificate_management"),
     path(
        "exam-fee-payments/",
        views.exam_fee_payment_list,
        name="exam_fee_payment_list",
    ),
    path(
        "exam-fee-payments/add/",
        views.exam_fee_payment_create,
        name="exam_fee_payment_create",
    ),
    path(
        "exam-fee-payments/<int:payment_id>/verify/",
        views.exam_fee_payment_verify,
        name="exam_fee_payment_verify",
    ),
    
path(
    "subject-management/",
    views.subject_management,
    name="subject_management",
),
path(
    "subject-management/add/",
    views.subject_create,
    name="subject_create",
),
path(
    "subject-management/<int:subject_id>/edit/",
    views.subject_edit,
    name="subject_edit",
),
path(
    "subject-management/<int:subject_id>/delete/",
    views.subject_delete,
    name="subject_delete",
),
path(
        "exam-schedule/",
        views.exam_schedule_list,
        name="exam_schedule_list",
    ),

    path(
        "exam-schedule/add/",
        views.exam_schedule_create,
        name="exam_schedule_create",
    ),

    path(
        "exam-schedule/<int:schedule_id>/edit/",
        views.exam_schedule_edit,
        name="exam_schedule_edit",
    ),

    path(
        "exam-schedule/<int:schedule_id>/delete/",
        views.exam_schedule_delete,
        name="exam_schedule_delete",
    ),
    path(
    "exam-centres/",
    views.exam_centres_list,
    name="exam_centres_list",
),
path(
    "exam-centres/add/",
    views.exam_centre_create,
    name="exam_centre_create",
),
path(
    "exam-centres/<int:centre_id>/edit/",
    views.exam_centre_edit,
    name="exam_centre_edit",
),
path(
    "exam-centres/<int:centre_id>/delete/",
    views.exam_centre_delete,
    name="exam_centre_delete",
),
path(
    "hall-tickets/",
    views.hall_ticket_management,
    name="hall_ticket_management",
),
path(
    "hall-tickets/generate/",
    views.hall_ticket_create,
    name="hall_ticket_create",
),
path(
    "hall-tickets/<int:ticket_id>/download/",
    views.hall_ticket_download,
    name="hall_ticket_download",
),
path(
    "hall-tickets/<int:ticket_id>/revoke/",
    views.hall_ticket_revoke,
    name="hall_ticket_revoke",
),
path(
        "examination-results/",
        views.examination_results,
        name="examination_results",
    ),
    path(
        "examination-results/calculate/<int:application_id>/",
        views.examination_result_calculate,
        name="examination_result_calculate",
    ),
    path(
        "examination-results/publish/<int:result_id>/",
        views.examination_result_publish,
        name="examination_result_publish",
    ),
   path(
    'students/<int:pk>/delete/confirm/',
    views.student_delete_confirm,
    name='student_delete_confirm'
),

path(
    'students/<int:pk>/delete/',
    views.student_delete,
    name='student_delete'
),


]
