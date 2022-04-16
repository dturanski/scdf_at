import logging, json, time,re
from shell.core import Shell, Utils
from cloudfoundry.domain import App, Service


logger = logging.getLogger(__name__)


class CloudFoundry:
    initialized = False

    @classmethod
    def connect(cls, deployer_config):
        logger.debug("ConnectionConfig:" + json.dumps(deployer_config))
        cf = CloudFoundry(deployer_config)

        if not CloudFoundry.initialized:
            logger.debug("logging in to CF: api %s org %s space %s" % (deployer_config.api_endpoint, deployer_config.org, deployer_config.space))
            proc = cf.login()
            if proc.returncode != 0:
                logger.error("CF login failed:" + Utils.stdout_to_s(proc))
                cf.logout()
                raise RuntimeError(
                    "cf login failed for some reason. Verify the username/password and that org %s and space %s exist"
                    % (deployer_config.org, deployer_config.space))
            logger.info("\n" + json.dumps(cf.current_target()))
            CloudFoundry.initialized = True
        else:
            logger.debug("Already logged in. Call 'cf logout'")
        return cf

    def __init__(self, deployer_config, shell=None):
        if not deployer_config:
            raise ValueError("'deployer_config' is required")
        self.deployer_config = deployer_config
        if shell:
            self.shell = shell
        else:
            self.shell = Shell()
        try:
            self.shell.exec('cf --version')
        except Exception:
            raise RuntimeError('cf cli is not installed')

        target = self.current_target()
        if target and target['api endpoint'] == deployer_config.api_endpoint and target['org'] == deployer_config.org and target[
            'space'] == deployer_config.space:
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
        if self.deployer_config.skip_ssl_validation:
            skip_ssl = "--skip-ssl-validation"

        cmd = "cf login -a %s -o %s -s %s -u %s -p %s %s" % \
              (self.deployer_config.api_endpoint,
               self.deployer_config.org,
               self.deployer_config.space,
               self.deployer_config.username,
               self.deployer_config.password,
               skip_ssl)
        return self.shell.exec(cmd)


    def create_service(self, config, service_config):
        logger.info("creating service " + json.dumps(service_config))

        proc = self.shell.exec("cf create-service %s %s %s %s" %
                               (service_config.service, service_config.plan, service_config.name,
                                "-c '%s'" % service_config.config if service_config.config else ""))
        Utils.log_stdout(proc)
        if self.shell.dry_run:
            return proc

        tries = 0
        service = self.service(service_config.name)
        # TODO:  pull this out to a common function
        while service.status != 'create succeeded' and tries < config.max_retries:
            time.sleep(config.deploy_wait_sec)
            tries = tries + 1
            logging.info("waiting %d/%d for service %s" % (tries, config.max_retries, json.dumps(service)))
            service = self.service(service_config.name)

        if service.status != 'create succeeded':
            raise SystemExit("maximum tries %d exceeded waiting for service %s" %
                             (config.max_retries, json.dumps(service)))
        else:
            logging.info("Created:" + json.dumps(service))
        return proc

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
            logger.error("service %s does not exist, or there is some other issue.")
            return None

        contents = Utils.stdout_to_s(proc)
        pattern = re.compile('(.+)\:\s+(.*)')
        s = {}
        for line in contents.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                s[match[1].strip()] = match[2].strip()

        return Service(name = s.get('name'),
                       service=s.get('service'),
                       plan=s.get('plan'),
                       status = s.get('status'),
                       message=s.get('message'))

    def services(self):
        logger.debug("getting services")
        proc = self.shell.exec("cf services")
        contents = Utils.stdout_to_s(proc)
        services = []
        parse_line = False
        for line in contents.split('\n'):
            # Brittle to scrape the text output directly, just grab the name and call `cf service` for each.
            # See self.service().
            if line.strip():
                if line.startswith('name'):
                    parse_line = True

                elif parse_line:
                    row = line.split(' ')
                    services.append(self.service(row[0]))

        logger.debug("services:\n" + json.dumps(services, indent=4))
        return services