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
#include <linux/device.h>

static int __init init(void)
{
	struct module *cur_module;
	struct class *cur_class;
	dev_t *dev;
	const struct file_operations *fops;
	unsigned int baseminor, count;
	struct usb_gadget_driver *cur_driver;

	cur_class = class_create(cur_module, "test");
	if (IS_ERR(cur_class)) {
		return -10;
	}
	class_destroy(cur_class);

	if (class_register(cur_class) == 0) {
		class_destroy(cur_class);
	}

	return 0;
}

module_init(init);