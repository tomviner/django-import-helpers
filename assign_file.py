
def assign_file_to_model(module, model_class=None, file_field='main_image', source_field='body', skip_existing=True, verbose=False):
    """ We tend to have "main image" fields on models that hold a primary image used
    across the sites for things like list pages and headers. Often on import of
    existing data we have images mangled within copy or lists. """

    import urllib2
    from posixpath import basename
    from BeautifulSoup import BeautifulSoup as Soup
    from django.db import IntegrityError
    from django.core.files import File

    if model_class is None:
        model_class = module.capitalize()

    mod = __import__(module)
    model= getattr(getattr(mod, 'models'), model_class)

    items = model.objects.all()

    for item in items:

        if getattr(item, file_field) and skip_existing:
            if verbose:
                print "Skipped %s" % item
            continue

        if verbose:
            print '\n%s' % item

        imgs = Soup(getattr(item, source_field)).findAll('img')
        if not imgs:
            if verbose:
                print 'No image found in source_field content'
            continue

        img_src = None
        for i, img in enumerate(imgs):
            img_src = img['src']
            if img.get('width', '')=='1' or img.get('height', '')=='1':
                continue
            file_path = '/tmp/%s' % basename(img_src)
            with open(file_path, 'w') as fd:
                try:
                    fd.write(urllib2.urlopen(img_src).read())
                except urllib2.HTTPError, e:
                    if e.code==404:
                        if verbose:
                            print 'Remote image number %d file not found' % (i+1)
                        continue # to try next image
                    else:
                        raise e
                else:
                    if verbose:
                        if i>0:
                            print 'Image number %s used' %(i+1)
                    break # no need to look at further images

        if img_src is None:
            if verbose:
                print 'No working images found after looking through %d' % (i+1)
            continue

        try:
            f = File(open(file_path))
            item.main_image = f
            item.save()
        except IntegrityError:
            if verbose:
                print "Error settings for %s" % item
            else:
                pass

        if verbose:
            print "Downloaded to %s" % (file_path)

    if verbose:
        print "Completed all %d %s items" % (items.count(), model.__name__)
