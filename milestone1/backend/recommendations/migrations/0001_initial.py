# Generated migration
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("candidate", "0005_merge_20260812_0513"),
        ("recruiter", "0005_interview"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="JobRecommendation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("match_score", models.FloatField(help_text="Overall match percentage (0-100)")),
                ("skill_match_score", models.FloatField(help_text="Skill match percentage (0-100)")),
                ("matched_skills", models.JSONField(default=list)),
                ("missing_skills", models.JSONField(default=list)),
                ("reason", models.TextField(help_text="Explanation of why this job was recommended")),
                ("is_viewed", models.BooleanField(default=False)),
                ("is_dismissed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="job_recommendations", to=settings.AUTH_USER_MODEL)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidate_recommendations", to="recruiter.job")),
            ],
            options={
                "ordering": ["-match_score", "-created_at"],
                "unique_together": {("candidate", "job")},
            },
        ),
        migrations.CreateModel(
            name="CandidateRecommendation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("match_score", models.FloatField(help_text="Overall match percentage (0-100)")),
                ("skill_match_score", models.FloatField(help_text="Skill match percentage (0-100)")),
                ("matched_skills", models.JSONField(default=list)),
                ("missing_skills", models.JSONField(default=list)),
                ("experience_match", models.BooleanField(default=False)),
                ("reason", models.TextField(help_text="Explanation of why this candidate was recommended")),
                ("is_viewed", models.BooleanField(default=False)),
                ("is_dismissed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recruiter_recommendations", to=settings.AUTH_USER_MODEL)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidate_recommendations", to="recruiter.job")),
            ],
            options={
                "ordering": ["-match_score", "-created_at"],
                "unique_together": {("job", "candidate")},
            },
        ),
    ]