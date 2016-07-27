#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/usb/gadget.h>

static int __init init(void)
{
	struct class *cur_class;
	struct usb_gadget_driver *cur_driver;

	// All at once.
	if (!usb_gadget_probe_driver(cur_driver)) {
		if (class_register(cur_class) == 0) {
			class_unregister(cur_class);
		}
		usb_gadget_unregister_driver(cur_driver);
	}
	return 0;
}

module_init(init);
