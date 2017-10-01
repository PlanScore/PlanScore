#!/usr/bin/env python
import planscore.website

if __name__ == '__main__':
    planscore.website.app.jinja_env.auto_reload = True
    planscore.website.app.config['TEMPLATES_AUTO_RELOAD'] = True
    planscore.website.app.run(debug=True)
