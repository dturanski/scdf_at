import logging, json, re
from shell.core import Shell, Utils
from cloudfoundry.domain import App, Service

logger = logging.getLogger(__name__)


class CloudFoundry:
    initialized = False

    def __init__(self, config, shell=None):
        if not config:
            raise ValueError("'config' is required")
        self.config = config
        if shell:
            self.shell = shell
        else:
            self.shell = Shell()
        try:
            self.shell.exec('cf --version')
        except Exception:
            raise RuntimeError('cf cli is not installed')

        target = self.current_target()
        if target and target['api endpoint'] == config.api_endpoint and target['org'] == config.org and target[
            'space'] == config.space:
            CloudFoundry.initialized = True

    def current_target(self):
        proc = self.shell.exec("cf target")
        contents = Utils.stdout_to_s(proc)
        target = {}
        for line in contents.split('\n'):
            if line:
                key = line[0:line.index(':')].strip()
                value = line[line.index(':') + 1:].strip()
                target[key] = value
        logger.debug("current context" + str(target))
        return target

    def target(self, org=None, space=None):
        cmd = "cf target"
        if org is not None:
            cmd = cmd + " -o %s" % (org)
        if space is not None:
            cmd = cmd + " -s %s" % (space)
        return self.shell.exec(cmd)

    def push(self, args):
        cmd = 'cf push ' + args
        return self.shell.exec(cmd)

    def is_logged_in(self):
        proc = self.shell.exec("cf target")
        info = Utils.stdout_to_s(proc)

        return proc.returncode == 0

    def logout(self):
        proc = self.shell.exec("cf logout")
        if proc.returncode == 0:
            CloudFoundry.initialized = False
        return proc

    def login(self):
        skip_ssl = ""
        if self.config.skip_ssl_validation:
            skip_ssl = "--skip-ssl-validation"

        cmd = "cf login -a %s -o %s -s %s -u %s -p %s %s" % \
              (self.config.api_endpoint,
               self.config.org,
               self.config.space,
               self.config.username,
               self.config.password,
               skip_ssl)
        return self.shell.exec(cmd)

    @classmethod
    def connect(cls, config):

        cf = CloudFoundry(config)

        if not CloudFoundry.initialized:
            logger.debug("logging in to CF: api %s org %s space %s" % (config.api_endpoint, config.org, config.space))
            proc = cf.login()
            if proc.returncode != 0:
                logger.error("CF login failed:" + Utils.stdout_to_s(proc))
                cf.logout()
                raise RuntimeError(
                    "cf login failed for some reason. Verify the username/password and that org %s and space %s exist"
                    % (config.org, config.space))
            logger.info("\n" + json.dumps(cf.current_target()))
            CloudFoundry.initialized = True
        else:
            logger.debug("Already logged in. Call 'cf logout'")
        return cf

    def create_service(self):
        pass

    def delete_service(self):
        pass

    def create_service_key(self):
        pass

    def delete_service_key(self):
        pass

    def apps(self):
        appnames = []
        proc = self.shell.exec("cf apps")
        contents = Utils.stdout_to_s(proc)
        i = 0
        for line in contents.split("\n"):
            if i > 3 and line:
                appnames.append(line.split(' ')[0])
            i = i + 1
        return appnames

    def delete_app(self, app_id):
        pass

    def delete_all(self, apps):
        for app in apps:
            proc = self.shell.exec("cf delete -f %s" % app)
            Utils.log_command(proc, "executed");

    def service(self,service_name):
        proc = self.shell.exec("cf service " + service_name)
        if proc.returncode != 0:
            logger.error("service %s does not exist, or some other issue.")
            return None

        contents = Utils.stdout_to_s(proc)
        pattern = re.compile('(.+)\:\s+(.*)')
        s = {}
        for line in contents.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                print(match[1].strip()+":" + match[2].strip())
                s[match[1].strip()] = match[2].strip()
        print(s)
        return Service(name = s['name'], service=s['service'],plan=s['plan'], status = s['status'], message=s.get('message'))


    def services(self):
        logger.debug("getting services")
        proc = self.shell.exec("cf services")
        contents = Utils.stdout_to_s(proc)
        services = []
        parse_line = False
        headers=[]
        for line in contents.split('\n'):
            # Brittle to scrape the text output without knowing all possible values, 2 or more spaces between fields, which may contain a space.
            logger.debug(line)
            if line.strip():
                if line.startswith('name'):
                    line = re.sub('\s{2,}', '~', line)
                    headers = line.split('~')
                    parse_line = True

                elif parse_line:
                    line = re.sub('\s{2,}', '~', line)
                    row = line.split('~')
                    services.append(self.service(row[0]))


        logger.debug("services:\n" + json.dumps(services, indent=4))
        return services