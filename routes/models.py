from django.db import models

class Routes(models.Model):
  org_code = models.TextField('Origin Code')
  dest_code = models.TextField('Destination Code')
  org_full = models.TextField('Origin Name', blank=True, null=True)
  dest_full = models.TextField('Destination Name', blank=True, null=True)

  def __unicode__(self):
    return "%s%s" % (self.org_code,self.dest_code)
