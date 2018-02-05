/*
 * Copyright (c) 2014-2016 ISPRAS (http://www.ispras.ru)
 * Institute for System Programming of the Russian Academy of Sciences
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * ee the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <linux/module.h>
#include <linux/net.h>
#include <linux/emg/test_model.h>
#include <verifier/nondet.h>

int flip_a_coin;

int ldv_create(struct net *net, struct socket *sock, int protocol, int kern)
{
	ldv_invoke_callback();
	return 0;
}

static struct net_proto_family ldv_driver = {
    .family = 5,
	.create = ldv_create
};

static int __init ldv_init(void)
{
    int ret = 0;
	flip_a_coin = ldv_undef_int();
	if (flip_a_coin) {
		ldv_register();
		ret = sock_register(& ldv_driver);
		if (ret)
		    ldv_deregister();
	}
	return ret;
}

static void __exit ldv_exit(void)
{
	if (flip_a_coin) {
		sock_unregister(5);
		ldv_deregister();
	}
}

module_init(ldv_init);
module_exit(ldv_exit);