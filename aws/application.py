#
# Wire
# Copyright (C) 2016 Wire Swiss GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#

# coding: utf-8

from datetime import datetime

import flask
import logging

from libs import flask_sslify
import config
import main
import util


application = main.MyFlask(__name__, static_url_path='')
application.config.from_object(config)
application.jinja_env.line_statement_prefix = '#'

# Remove this line in case you want to skip the automatic redirect to HTTPS
sslify = flask_sslify.SSLify(application, skips=['test'])


###############################################################################
# Controllers
###############################################################################
@application.route('/<path>/')
@application.route('/')
@main.latest_browser_required
def index(path=None):
  return flask.make_response(flask.render_template('index.html'))


@application.route('/auth/')
@main.latest_browser_required
def auth():
  response = flask.make_response(flask.render_template(
    'auth/index.html',
    country=util.geoip_country(),
  ))
  return response



@application.route('/robots.txt')
def robots_txt():
  response = flask.make_response(flask.render_template('robots.txt'))
  response.headers['Content-Type'] = 'text/plain'
  return response


@application.route('/sitemap.xml')
def sitemap_xml():
  response = flask.make_response(flask.render_template(
      'sitemap.xml',
      lastmod=datetime.today().strftime('%Y-%m-%d'),
    ))
  response.headers['Content-Type'] = 'application/xml'
  return response


@application.route('/browser/')
@main.latest_browser_required
def browser_test():
  return flask.jsonify(util.user_agent())


@application.route('/test/')
def test():
  response = flask.make_response(flask.render_template(
      'aws/debug.html',
      title='Test',
      agent=util.user_agent(),
      timestamp=datetime.utcnow(),
      get_url=util.get_url(),
      host=flask.request.host,
      country=util.geoip_country(),
      ip=flask.request.headers.get('X-Forwarded-For') or flask.request.remote_addr,
    ))
  return response


@application.route('/test/agent/')
def test_agent():
  return flask.jsonify(util.user_agent())


@application.route('/test/agent/raw/')
def test_agent_raw():
  response = flask.make_response(flask.request.headers['User-Agent'])
  return response


@application.route('/test/<int:error>/')
def test_error(error):
  if error in [400, 401, 403, 405, 406, 410, 418, 500]:
    flask.abort(error)
  flask.abort(404)


@application.route('/demo/')
def demo():
  return flask.make_response(flask.render_template(
    'demo/index.html',
  ))


###############################################################################
# Error Stuff
###############################################################################
@application.errorhandler(400)  # Bad Request
@application.errorhandler(401)  # Unauthorized
@application.errorhandler(403)  # Forbidden
@application.errorhandler(404)  # Not Found
@application.errorhandler(405)  # Method Not Allowed
@application.errorhandler(406)  # Unsupported Browsers
@application.errorhandler(410)  # Gone
@application.errorhandler(418)  # I'm a Teapot
@application.errorhandler(500)  # Internal Server Error
def error_handler(e):
  try:
    e.code
  except AttributeError:
    e.code = 500
    e.name = 'Internal Server Error'

  handler = logging.StreamHandler()
  application.logger.addHandler(handler)
  application.logger.error('-=' * 40)
  application.logger.error(flask.request.url)
  application.logger.error('-=' * 40)
  application.logger.exception(e)

  if e.code == 406:
    return flask.redirect('https://wire.com/unsupported/')

  return flask.render_template(
      'aws/error.html',
      title='Error %d (%s)!!1' % (e.code, e.name),
      error=e,
      timestamp=datetime.utcnow(),
    ), e.code


###############################################################################
# Main :)
###############################################################################
if __name__ == '__main__':
  application.run(host='0.0.0.0')
