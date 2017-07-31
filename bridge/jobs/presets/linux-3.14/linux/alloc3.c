#include <linux/gfp.h>
#include <verifier/common.h>
#include <verifier/nondet.h>

struct usb_device;

/* CHANGE_STATE USB lock is not acquired at the beginning */
int ldv_lock = 1;

/* MODEL_FUNC_DEF Check that correct flag was used when USB lock is aquired */
void ldv_check_alloc_flags(gfp_t flags) 
{
	if (ldv_lock == 2)
	{
		/* ASSERT GFP_NOIO or GFP_ATOMIC flag should be used when USB lock is aquired */
		ldv_assert("linux:alloc:usb lock::wrong flags", flags == GFP_NOIO || flags == GFP_ATOMIC);
	}
}

/* MODEL_FUNC_DEF Check that USB lock is not acquired */
void ldv_check_alloc_nonatomic(void)
{
	/* ASSERT USB lock should not be acquired */
	ldv_assert("linux:alloc:usb lock::nonatomic", ldv_lock == 1);
}

/* MODEL_FUNC_DEF Acquire USB lock */
void ldv_usb_lock_device(void)
{
	/* CHANGE_STATE Acquire USB lock */
	ldv_lock = 2;
}

/* MODEL_FUNC_DEF Try to acquire USB lock */
int ldv_usb_trylock_device(struct usb_device *udev)
{
	if (ldv_lock == 1 && ldv_undef_int())
	{
		/* CHANGE_STATE Acquire USB lock */
		ldv_lock = 2;
		/* RETURN USB lock was acquired */
		return 1;
	}
	else
	{
		/* RETURN USB lock was not acquired */
		return 0;
	}
}

/* MODEL_FUNC_DEF Try to acquire USB lock */
int ldv_usb_lock_device_for_reset(struct usb_device *udev)
{
	if (ldv_lock == 1 && ldv_undef_int())
	{
		/* CHANGE_STATE Acquire USB lock */
		ldv_lock = 2;
		/* RETURN USB lock was acquired */
		return 0;
	}
	else
	{
		/* RETURN USB lock wad not acquired */
		return -1;
	}
}

/* MODEL_FUNC_DEF Release USB lock */
void ldv_usb_unlock_device(void)
{
	/* CHANGE_STATE Release USB lock */
	ldv_lock = 1;
}