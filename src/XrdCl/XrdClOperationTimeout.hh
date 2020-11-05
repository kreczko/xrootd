/*
 * XrdClOperationTimeout.hh
 *
 *  Created on: 4 Nov 2020
 *      Author: simonm
 */

#ifndef SRC_XRDCL_XRDCLOPERATIONTIMEOUT_HH_
#define SRC_XRDCL_XRDCLOPERATIONTIMEOUT_HH_

#include <stdint.h>
#include <time.h>

class Timeout
{
  public:

    Timeout(): timeout( 0 ), start( 0 )
    {
    }

    Timeout( uint16_t timeout ): timeout( timeout ), start( time( 0 ) )
    {
    }

    Timeout( const Timeout &to ) : timeout( to.timeout ), start( to.start )
    {
    }

    operator uint16_t() const
    {
      if( !timeout ) return 0;
      time_t elapsed = time( 0 ) - start;
      if( timeout < elapsed) throw std::exception(); // TODO
      return timeout - elapsed;
    }

  private:

    uint16_t timeout;
    time_t   start;
};



#endif /* SRC_XRDCL_XRDCLOPERATIONTIMEOUT_HH_ */
