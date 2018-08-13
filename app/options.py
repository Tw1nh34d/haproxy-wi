#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
import html
import cgi
import os, sys
import funct
import sql
import ovw

form = cgi.FieldStorage()
req = form.getvalue('req')
serv = form.getvalue('serv')
act = form.getvalue('act')
backend = form.getvalue('backend')	
	
print('Content-type: text/html\n')

if form.getvalue('token') is None:
	print("What the fuck?! U r hacker Oo?!")
	sys.exit()
	
if form.getvalue('getcerts') is not None and serv is not None:
	cert_path = sql.get_setting('cert_path')
	commands = [ "ls -1t "+cert_path+" |grep pem" ]
	try:
		funct.ssh_command(serv, commands, ip="1")
	except:
		print('<div class="alert alert-danger" style="margin:0">Can not connect to the server</div>')
		
if form.getvalue('getcert') is not None and serv is not None:
	id = form.getvalue('getcert')
	cert_path = sql.get_setting('cert_path')
	commands = [ "cat "+cert_path+"/"+id ]
	try:
		funct.ssh_command(serv, commands, ip="1")
	except:
		print('<div class="alert alert-danger" style="margin:0">Can not connect to the server</div>')
		
if form.getvalue('ssh_cert'):
	name = form.getvalue('name')
	ssh_keys = os.path.dirname(os.getcwd())+'/keys/'+name+'.pem'
	
	try:
		with open(ssh_keys, "w") as conf:
			conf.write(form.getvalue('ssh_cert'))
	except IOError:
		print('<div class="alert alert-danger">Can\'t save ssh keys file. Check ssh keys path in config</div>')
	else:
		print('<div class="alert alert-success">Ssh key was save into: %s </div>' % ssh_keys)
	try:
		funct.logging("local", "users.py#ssh upload new ssh cert %s" % ssh_keys)
	except:
		pass
			
if serv and form.getvalue('ssl_cert'):
	cert_local_dir = funct.get_config_var('main', 'cert_local_dir')
	cert_path = sql.get_setting('cert_path')
	
	if form.getvalue('ssl_name') is None:
		print('<div class="alert alert-danger">Please enter desired name</div>')
	else:
		name = form.getvalue('ssl_name') + '.pem'
	
	try:
		with open(name, "w") as ssl_cert:
			ssl_cert.write(form.getvalue('ssl_cert'))
	except IOError:
		print('<div class="alert alert-danger">Can\'t save ssl keys file. Check ssh keys path in config</div>')
	else:
		print('<div class="alert alert-success">SSL file was upload to %s into: %s </div>' % (serv, cert_path))
		
	MASTERS = sql.is_master(serv)
	for master in MASTERS:
		if master[0] != None:
			funct.upload(master[0], cert_path, name)
	try:
		funct.upload(serv, cert_path, name)
	except:
		pass
	
	os.system("mv %s %s" % (name, cert_local_dir))
	funct.logging(serv, "add.py#ssl upload new ssl cert %s" % name)
	
if backend is not None:
	funct.show_backends(serv)
	
if form.getvalue('ip') is not None and serv is not None:
	commands = [ "sudo ip a |grep inet |egrep -v  '::1' |awk '{ print $2  }' |awk -F'/' '{ print $1  }'" ]
	funct.ssh_command(serv, commands, ip="1")
	
if form.getvalue('showif'):
	commands = ["sudo ip link|grep 'UP' | awk '{print $2}'  |awk -F':' '{print $1}'"]
	funct.ssh_command(serv, commands, ip="1")
	
if form.getvalue('action_hap') is not None and serv is not None:
	serv = form.getvalue('serv')
	action = form.getvalue('action_hap')
	
	if funct.check_haproxy_config(serv):
		commands = [ "sudo systemctl %s haproxy" % action ]
		funct.ssh_command(serv, commands)		
		print("HAproxy was %s" % action)
	else:
		print("Bad config, check please")
		
if act == "overview":
	ovw.get_overview()

if act == "overviewServers":
	ovw.get_overviewServers()
	
if form.getvalue('action'):
	import requests
	from requests_toolbelt.utils import dump
	
	haproxy_user = sql.get_setting('stats_user')
	haproxy_pass = sql.get_setting('stats_password')
	stats_port = sql.get_setting('stats_port')
	stats_page = sql.get_setting('stats_page')
	
	postdata = {
		'action' : form.getvalue('action'),
		's' : form.getvalue('s'),
		'b' : form.getvalue('b')
	}

	headers = {
		'User-Agent' : 'Mozilla/5.0 (Windows NT 5.1; rv:20.0) Gecko/20100101 Firefox/20.0',
		'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language' : 'en-US,en;q=0.5',
		'Accept-Encoding' : 'gzip, deflate'
	}

	q = requests.post('http://'+serv+':'+stats_port+'/'+stats_page, headers=headers, data=postdata, auth=(haproxy_user, haproxy_pass))
	
if serv is not None and act == "stats":
	import requests
	from requests_toolbelt.utils import dump
	
	haproxy_user = sql.get_setting('stats_user')
	haproxy_pass = sql.get_setting('stats_password')
	stats_port = sql.get_setting('stats_port')
	stats_page = sql.get_setting('stats_page')
	try:
		response = requests.get('http://%s:%s/%s' % (serv, stats_port, stats_page), auth=(haproxy_user, haproxy_pass)) 
	except requests.exceptions.ConnectTimeout:
		print('Oops. Connection timeout occured!')
	except requests.exceptions.ReadTimeout:
		print('Oops. Read timeout occured')
	except requests.exceptions.HTTPError as errh:
		print ("Http Error:",errh)
	except requests.exceptions.ConnectionError as errc:
		print ('<div class="alert alert-danger">Error Connecting: %s</div>' % errc)
	except requests.exceptions.Timeout as errt:
		print ("Timeout Error:",errt)
	except requests.exceptions.RequestException as err:
		print ("OOps: Something Else",err)
		
	data = response.content
	print(data.decode('utf-8'))

if serv is not None and form.getvalue('rows') is not None:
	rows = form.getvalue('rows')
	grep = form.getvalue('grep')
	hour = form.getvalue('hour')
	minut = form.getvalue('minut')
	hour1 = form.getvalue('hour1')
	minut1 = form.getvalue('minut1')
	date = hour+':'+minut
	date1 = hour1+':'+minut1
	
	if grep is not None:
        	grep_act  = '|grep'
	else:
		grep_act = ''
		grep = ''

	syslog_server_enable = sql.get_setting('syslog_server_enable')
	if syslog_server_enable is None or syslog_server_enable == "0":
		local_path_logs = sql.get_setting('local_path_logs')
		syslog_server = serv	
		commands = [ "sudo cat %s| awk '$3>\"%s:00\" && $3<\"%s:00\"' |tail -%s  %s %s" % (local_path_logs, date, date1, rows, grep_act, grep) ]	
	else:
		commands = [ "sudo cat /var/log/%s/syslog.log | sed '/ %s:00/,/ %s:00/! d' |tail -%s  %s %s" % (serv, date, date1, rows, grep_act, grep) ]
		syslog_server = sql.get_setting('syslog_server')

	funct.ssh_command(syslog_server, commands, show_log="1")
	
if serv is not None and form.getvalue('rows1') is not None:
	rows = form.getvalue('rows1')
	grep = form.getvalue('grep')
	hour = form.getvalue('hour')
	minut = form.getvalue('minut')
	hour1 = form.getvalue('hour1')
	minut1 = form.getvalue('minut1')
	date = hour+':'+minut
	date1 = hour1+':'+minut1
	
	if grep is not None:
		grep_act  = '|grep'
	else:
		grep_act = ''
		grep = ''
		
	if serv == 'haproxy-wi.access.log':
		cmd="cat %s| awk -F\"/|:\" '$3>\"%s:00\" && $3<\"%s:00\"' |tail -%s  %s %s" % ('/var/log/httpd/'+serv, date, date1, rows, grep_act, grep)
	else:
		cmd="cat %s| awk '$4>\"%s:00\" && $4<\"%s:00\"' |tail -%s  %s %s" % ('/var/log/httpd/'+serv, date, date1, rows, grep_act, grep)

	output, stderr = funct.subprocess_execute(cmd)

	funct.show_log(output)
	print(stderr)
		
if form.getvalue('viewlogs') is not None:
	viewlog = form.getvalue('viewlogs')
	log_path = funct.get_config_var('main', 'log_path')
	rows = form.getvalue('rows2')
	grep = form.getvalue('grep')
	hour = form.getvalue('hour')
	minut = form.getvalue('minut')
	hour1 = form.getvalue('hour1')
	minut1 = form.getvalue('minut1')
	date = hour+':'+minut
	date1 = hour1+':'+minut1
	
	if grep is not None:
		grep_act  = '|grep'
	else:
		grep_act = ''
		grep = ''

	cmd="cat %s| awk '$3>\"%s:00\" && $3<\"%s:00\"' |tail -%s  %s %s" % (log_path + viewlog, date, date1, rows, grep_act, grep)
	output, stderr = funct.subprocess_execute(cmd)

	funct.show_log(output)
	print(stderr)
		
if serv is not None and act == "showMap":
	ovw.get_map(serv)
	
if form.getvalue('servaction') is not None:
	server_state_file = sql.get_setting('server_state_file')
	haproxy_sock = sql.get_setting('haproxy_sock')
	enable = form.getvalue('servaction')
	backend = form.getvalue('servbackend')
	
	cmd='echo "%s %s" |sudo socat stdio %s | cut -d "," -f 1-2,5-10,18,34-36 | column -s, -t' % (enable, backend, haproxy_sock)
	
	if form.getvalue('save') == "on":
		save_command = 'echo "show servers state" | sudo socat stdio %s > %s' % (haproxy_sock, server_state_file)
		command = [ cmd, save_command ] 
	else:
		command = [ cmd ] 
		
	if enable != "show":
			print('<center><h3>You %s %s on HAproxy %s. <a href="viewsttats.py?serv=%s" title="View stat" target="_blank">Look it</a> or <a href="edit.py" title="Edit">Edit something else</a></h3><br />' % (enable, backend, serv, serv))
			
	funct.ssh_command(serv, command, show_log="1")
	action = 'edit.py ' + enable + ' ' + backend
	funct.logging(serv, action)

if act == "showCompareConfigs":
	ovw.show_compare_configs(serv)
	
if serv is not None and form.getvalue('right') is not None:
	ovw.comapre_show()
	
if serv is not None and act == "configShow":
	hap_configs_dir = funct.get_config_var('configs', 'haproxy_save_configs_dir')
	
	if form.getvalue('configver') is None:	
		cfg = hap_configs_dir + serv + "-" + funct.get_data('config') + ".cfg"
		funct.get_config(serv, cfg)
	else: 
		cfg = hap_configs_dir + form.getvalue('configver')
		
	print("<center><h3>Config from %s</h3>" % serv)
	print('<p class="accordion-expand-holder">'
			'<a class="accordion-expand-all ui-button ui-widget ui-corner-all" href="#">Expand all</a>'
			'<a class="ui-button ui-widget ui-corner-all" title="Edit this run config" target="_blank" href="config.py?serv='+serv+'&open=open">Edit</a>'
		'</p>')
	print('</center>')
	
	funct.show_config(cfg)
	
	if form.getvalue('configver') is None:
		os.system("/bin/rm -f " + cfg)	
	else:
		print('<br><center>')
		print('<form action="configver.py#conf" method="get">')
		print('<input type="hidden" value="%s" name="serv">' % serv)
		print('<input type="hidden" value="%s" name="configver">' % form.getvalue('configver'))
		print('<input type="hidden" value="1" name="config">')
		if form.getvalue('view') is None:
			print("<button type='submit' value='save' name='save' class='btn btn-default'>Just save</button>")
			print("<button type='submit' value='' name='' class='btn btn-default'>Upload and restart</button>")
		print('</form></center>')
		
if form.getvalue('master'):
	master = form.getvalue('master')
	slave = form.getvalue('slave')
	interface = form.getvalue('interface')
	vrrpip = form.getvalue('vrrpip')
	hap = form.getvalue('hap')
	syn_flood = form.getvalue('syn_flood')
	tmp_config_path = sql.get_setting('tmp_config_path')
	script = "install_keepalived.sh"
	
	if hap == "1":
		funct.install_haproxy(master)
		funct.install_haproxy(slave)
		
	if syn_flood == "1":
		funct.syn_flood_protect(master)
		funct.syn_flood_protect(slave)
	
	os.system("cp scripts/%s ." % script)
		
	funct.upload(master, tmp_config_path, script)
	funct.upload(slave, tmp_config_path, script)
	
	commands = [ "chmod +x "+tmp_config_path+script, tmp_config_path+script+" MASTER "+interface+" "+vrrpip ]
	funct.ssh_command(master, commands)
	
	commands = [ "chmod +x "+tmp_config_path+script, tmp_config_path+script+" BACKUP "+interface+" "+vrrpip ]
	funct.ssh_command(slave, commands)
			
	os.system("rm -f %s" % script)
	sql.update_server_master(master, slave)
	
if form.getvalue('masteradd'):
	master = form.getvalue('masteradd')
	slave = form.getvalue('slaveadd')
	interface = form.getvalue('interfaceadd')
	vrrpip = form.getvalue('vrrpipadd')
	kp = form.getvalue('kp')
	tmp_config_path = sql.get_setting('tmp_config_path')
	script = "add_vrrp.sh"
	
	os.system("cp scripts/%s ." % script)
		
	funct.upload(master, tmp_config_path, script)
	funct.upload(slave, tmp_config_path, script)
	
	commands = [ "sudo chmod +x "+tmp_config_path+script, tmp_config_path+script+" MASTER "+interface+" "+vrrpip+" "+kp]
	funct.ssh_command(master, commands)
	
	commands = [ "sudo chmod +x "+tmp_config_path+script, tmp_config_path+script+" BACKUP "+interface+" "+vrrpip+" "+kp ]
	funct.ssh_command(slave, commands)
			
	os.system("rm -f %s" % script)
	
if form.getvalue('haproxyaddserv'):
	funct.install_haproxy(form.getvalue('haproxyaddserv'), syn_flood=form.getvalue('syn_flood'))
	
if form.getvalue('table_metrics'):
	import http.cookies
	from jinja2 import Environment, FileSystemLoader
	env = Environment(loader=FileSystemLoader('templates/ajax'))
	template = env.get_template('table_metrics.html')
		
	cookie = http.cookies.SimpleCookie(os.environ.get("HTTP_COOKIE"))
	user_id = cookie.get('uuid')	
	table_stat = sql.select_table_metrics(user_id.value)

	template = template.render(table_stat = sql.select_table_metrics(user_id.value))											
	print(template)
		
if form.getvalue('metrics'):
	from datetime import timedelta
	from bokeh.plotting import figure, output_file, show
	from bokeh.models import ColumnDataSource, HoverTool, DatetimeTickFormatter, DatePicker
	from bokeh.layouts import widgetbox, gridplot
	from bokeh.models.widgets import Button, RadioButtonGroup, Select
	import pandas as pd
	import http.cookies
		
	cookie = http.cookies.SimpleCookie(os.environ.get("HTTP_COOKIE"))
	user_id = cookie.get('uuid')	
	servers = sql.select_servers_metrics(user_id.value)
	
	p = {}
	for serv in servers:
		serv = serv[0]
		p[serv] = {}
		metric = sql.select_metrics(serv)
		metrics = {}
		
		for i in metric:
			rep_date = str(i[5])
			metrics[rep_date] = {}
			metrics[rep_date]['server'] = str(i[0])
			metrics[rep_date]['curr_con'] = str(i[1])
			metrics[rep_date]['curr_ssl_con'] = str(i[2])
			metrics[rep_date]['sess_rate'] = str(i[3])
			metrics[rep_date]['max_sess_rate'] = str(i[4])

		df = pd.DataFrame.from_dict(metrics, orient="index")
		df = df.fillna(0)
		df.index = pd.to_datetime(df.index)
		df.index.name = 'Date'
		df.sort_index(inplace=True)
		source = ColumnDataSource(df)
		
		output_file("templates/metrics_out.html")
		
		x_min = df.index.min() - pd.Timedelta(hours=1)
		x_max = df.index.max() + pd.Timedelta(minutes=1)

		p[serv] = figure(
			tools="pan,box_zoom,reset,xwheel_zoom",
			title=metric[0][0],
			x_axis_type="datetime", y_axis_label='Connections',
			x_range = (x_max.timestamp()*1000-60*100000, x_max.timestamp()*1000)
			)
			
		hover = HoverTool(
			tooltips=[
				("Connections", "@curr_con"),
				("SSL connections", "@curr_ssl_con"),
				("Sessions rate", "@sess_rate")
			],
			mode='mouse'
		)
		
		p[serv].ygrid.band_fill_color = "#f3f8fb"
		p[serv].ygrid.band_fill_alpha = 0.9
		p[serv].y_range.start = 0
		p[serv].y_range.end = int(df['curr_con'].max()) + 150
		p[serv].add_tools(hover)
		p[serv].title.text_font_size = "20px"
				
		
		p[serv].line("Date", "curr_con", source=source, alpha=0.5, color='#5cb85c', line_width=2, legend="Conn")
		p[serv].line("Date", "curr_ssl_con", source=source, alpha=0.5, color="#5d9ceb", line_width=2, legend="SSL con")
		p[serv].line("Date", "sess_rate", source=source, alpha=0.5, color="#33414e", line_width=2, legend="Sessions")
		#p[serv].line("Date", "max_sess_rate", source=source, alpha=0.5, color="red", line_width=2, legend="Max sess")
		p[serv].legend.orientation = "horizontal"
		p[serv].legend.location = "top_left"
		p[serv].legend.padding = 5

			
	#select = Select(title="Option:", value="foo", options=["foo", "bar", "baz", "quux"])
	#show(widgetbox(select, width=300))
		
	plots = []
	i = 0
	for key, value in p.items():
		plots.append(value)

	grid = gridplot(plots, ncols=2, plot_width=800, plot_height=250, toolbar_location = "left", toolbar_options=dict(logo=None))
	show(grid)
	
if form.getvalue('get_hap_v'):
	commands = [ "haproxy -v |grep ver|awk '{print $3}'" ]
	output = funct.ssh_command(serv, commands)
	print(output)
	
if form.getvalue('bwlists'):
	list = os.path.dirname(os.getcwd())+"/"+sql.get_setting('lists_path')+"/"+form.getvalue('group')+"/"+form.getvalue('color')+"/"+form.getvalue('bwlists')
	try:
		file = open(list, "r")
		file_read = file.read()
		file.close
		print(file_read)
	except IOError:
		print('<div class="alert alert-danger" style="margin:0">Cat\'n read '+form.getvalue('color')+' list</div>')
		
if form.getvalue('bwlists_create'):
	list_name = form.getvalue('bwlists_create').split('.')[0]
	list_name += '.lst'
	list = os.path.dirname(os.getcwd())+"/"+sql.get_setting('lists_path')+"/"+form.getvalue('group')+"/"+form.getvalue('color')+"/"+list_name
	try:
		open(list, 'a').close()
		print('<div class="alert alert-success" style="margin:0">'+form.getvalue('color')+' list was created</div>')
	except IOError as e:
		print('<div class="alert alert-danger" style="margin:0">Cat\'n create new '+form.getvalue('color')+' list. %s </div>' % e)
		
if form.getvalue('bwlists_save'):
	list = os.path.dirname(os.getcwd())+"/"+sql.get_setting('lists_path')+"/"+form.getvalue('group')+"/"+form.getvalue('color')+"/"+form.getvalue('bwlists_save')
	try:
		with open(list, "w") as file:
			file.write(form.getvalue('bwlists_content'))
	except IOError as e:
		print('<div class="alert alert-danger" style="margin:0">Cat\'n save '+form.getvalue('color')+' list. %s </div>' % e)
	
	servers = sql.get_dick_permit()
	path = sql.get_setting('haproxy_dir')+"/"+form.getvalue('color')
	
	for server in servers:
		commands = [ "sudo mkdir "+path ]
		funct.ssh_command(server[2], commands)
		
		try:
			ssh = funct.ssh_connect(server[2])
		except Exception as e:
			print('<div class="alert alert-danger">Connect fail: %s</div>' % e)
			
		try:
			sftp = ssh.open_sftp()
			file = sftp.put(list, path+"/"+form.getvalue('bwlists_save'))
			sftp.close()
			ssh.close()
			print('<div class="alert alert-success" style="margin:10px">Edited '+form.getvalue('color')+' list was uploaded to '+server[1]+'</div>')
		except Exception as e:
			print('<div class="alert alert-danger">Upload fail: %s</div>' % e)
			
		if form.getvalue('bwlists_restart') == 'restart':
			commands = [ "sudo " + sql.get_setting('restart_command') ]
			funct.ssh_command(server[2], commands)
			
if form.getvalue('get_lists'):
	list = os.path.dirname(os.getcwd())+"/"+sql.get_setting('lists_path')+"/"+form.getvalue('group')+"/"+form.getvalue('color')
	lists = funct.get_files(dir=list, format="lst")
	for list in lists:
		print(list)