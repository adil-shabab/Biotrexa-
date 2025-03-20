from django.contrib.sitemaps import Sitemap
from .models import Department, Doctor, Blog, HealthCheckupPlan, Career, Gallery
from django.urls import reverse


class DepartmentSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Department.objects.filter(status='active')

    def lastmod(self, obj):
        return obj.updated_at


class DoctorSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Doctor.objects.filter(status='active')

    def lastmod(self, obj):
        return obj.updated_at

class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Blog.objects.filter(status='active')

    def lastmod(self, obj):
        return obj.createdAt


class HealthCheckupPlanSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return HealthCheckupPlan.objects.filter(status='active')

    def lastmod(self, obj):
        return obj.created_at


class CareerSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Career.objects.filter(status='active')

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return [
            'homepage', 'about', 'services', 'contact', 'gallery_list', 'frontend_careers', 
            'frontend_blogs', 'frontend_doctors', 'privacy_policy', 'terms_condition'
        ]

    def location(self, item):
        return reverse(item)
